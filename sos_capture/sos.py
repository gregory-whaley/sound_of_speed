#!/usr/bin/python
#  python script to capture stereo audio and compute speed of vehicle passing by.
#  G. Whaley
#  30 March 2024

import numpy as np
import sounddevice as sd
import png
from datetime import datetime
from datetime import timedelta
import sqlite3
import os
import sys
import yaml
import paho.mqtt.publish as mqtt
import zmq


with open('sos.config','r') as file:
    parms = yaml.safe_load(file)          # load config data

audio_input_selector = 'hw:'   # string descriptor for ALSA hardware device
if 'audio_input_selector' in parms:
    audio_input_selector = parms['audio_input_selector']
    
input_num = 0					#  integer index pointing to input device
if 'input_num' in parms:
    temp = int(parms['input_num'])
    if temp >= 0 and temp <=10:
        input_num = temp


buf_size = 1024*8				# size of signal buffer in samples
if 'frame_size' in parms:
    temp = int(parms['frame_size'])
    if temp in [128,256,512,1024,2048,4096,8192]:
        buf_size = temp

audio_samples = np.zeros([buf_size,2])  # data buffer for 2 channel stereo floats
audio_sample_rate = 48000
if 'audio_sample_rate' in parms:
    temp = int(parms['audio_sample_rate'])
    if temp >= 8000 and temp <= 48000:
        audio_sample_rate = temp

audio_DC = np.zeros(2)   # initialize DC average of audio signals
db_filename = 'speed.db'
if 'db_filename' in parms:
    db_filename = parms['db_filename']

# num_vectors = 100   # number of vectors to store for historical analysis
# if 'num_vectors' in parms:
#     temp = int(parms['num_vectors'])
#     if temp >=20 and temp <= 1000:
#         num_vectors = temp



mic_spacing = 0.53       # microphone spacing in meters
if 'mic_spacing' in parms:
    temp = float(parms['mic_spacing'])
    if temp > 0.0 and temp < 5.0:
        mic_spacing = temp

pos_sens_dist = 32.0         # distance from microphones to road in meters for positive speeds
if 'pos_sens_dist' in parms:
     temp = float(parms['pos_sens_dist'])
     if temp > 5 and temp < 100:
         pos_sens_dist = temp

neg_sense_dist = pos_sens_dist    # default is same distance (approxmation)
if 'neg_sens_dist' in parms:
     temp = float(parms['neg_sens_dist'])
     if temp > 5 and temp < 100:
         neg_sens_dist = temp

temperature = 0.0        # air temperature in C
if 'temperature' in parms:
    temp = float(parms['temperature'])
    if temp > -41 and temp < 50:
        temperature = temp

scale_factor = 10000.0 / float(buf_size)   # default clip level for correlation normalization factor
if 'noise_floor' in parms:				# larger values imply lower noise floor
    temp = float(parms['noise_floor'])
    if temp >= 100.0 and temp <= 100000.0:
        scale_factor = temp / float(buf_size)

delay_offset_samples = int(0)
if 'delay_offset_ms' in parms:
    temp = float(parms['delay_offset_ms'])
    if temp >= -1 and temp <= 1:
        delay_offset_samples = int(temp * float(audio_sample_rate) / 1000.0)     


min_speed = 15.0          # slowest measurable speed in MPH
if 'min_speed' in parms:
    temp = float(parms['min_speed'])
    if temp > 10 and temp < 30:
        min_speed = temp
        
max_speed = 60.0			# fastest measurable speed in MPH
if 'max_speed' in parms:
    temp = float(parms['max_speed'])
    if temp > 30 and temp < 80:
        max_speed = temp


context = zmq.Context()      # initialize the ZMQ publishing socket
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")


v_sound = 331.3 + temperature * 0.606   # speed of sound in m/s
frame_rate = float(audio_sample_rate)/buf_size   # frame rate in frames/sec.
span = int(0.80 * mic_spacing * audio_sample_rate / v_sound)  # use 80% of the total delay angle span in delay sample units, one-sided
center = int(buf_size/2) - delay_offset_samples      # center of discrete curves for overlap calculation, integer value.
num_vectors = 2 * int((1.4 * frame_rate * max(pos_sens_dist,neg_sens_dist)) / (min_speed * 0.447))   # allocate enough memory to store correlation history
                    # the 1.4 factor comes from the tan(asin(0.8)) value
ptr = 0              # points to current vector location in circular buffer
buffer = np.zeros((num_vectors,buf_size),dtype=np.float32)  # create buffer, fill with zero

num_samples = 2*span + 1                        # number of delay samples to compute overlap integral
p_col = np.zeros(num_samples,dtype=np.int32)     # points to column location in overlap buffer for positive speed curve
n_col = np.zeros(num_samples,dtype=np.int32)     # points to column location in overlap buffer for negative speed curve
for i in range(num_samples):
    p_col[i] = np.rint(center - span + i)   # samples in vector for positive speed curve
    n_col[i] = np.rint(center + span - i)   # samples for negative speed curve

num_speeds = 50                                    #  number of different trial speeds to compute overlap integral

speed = np.zeros(num_speeds,dtype=np.float32)      # allocate storage of range of speeds in array, units in m/s
    # the array 'row' stores an int which points to a location in the correlation buffer which is a valid overlap entry.
    # At each valid overlap point, the integral 1.0 * correlation value is added to the accumulator for that speed value.
p_overlap = np.zeros((num_vectors,num_speeds),dtype=np.float32)    # store overlap integral results for positive speeds
n_overlap = np.zeros((num_vectors,num_speeds),dtype=np.float32)

p_row=np.zeros((num_speeds,num_samples),dtype=np.int32)      # points to row location in buffer for all positive speed curves
n_row=np.zeros((num_speeds,num_samples),dtype=np.int32)      # points to row location in buffer for all negative speed curves

for i in range(num_speeds):
    speed[i]=0.447*(min_speed + (max_speed-min_speed)*float(i)/(num_speeds-1))      # array of speeds in m/s            
    p_row[i][:] = np.rint(num_vectors/2 + (frame_rate*pos_sens_dist/speed[i])*np.tan(np.arcsin((p_col[:]-center)*(v_sound/(audio_sample_rate*mic_spacing)))))
    n_row[i][:] = np.rint(num_vectors/2 + (frame_rate*neg_sens_dist/speed[i])*np.tan(np.arcsin((p_col[:]-center)*(v_sound/(audio_sample_rate*mic_spacing)))))
    # row[] is the set of offsets from the target row vector in the buffer for a given speed
    # with row[] and p_col[] I can index the samples of interest in the buffer and compute the overlap integral
    # 0.447 is conversion from m/s to MPH.
    # lowest speed is 15 MPH, highest speed is 55 MPH
    # num_vectors is the number frames in the correlation buffer, so num_vectors/2 points to the middle of the buffer for overlap calculation
    # the factors before the tan() function represent how many frames in the past would a vehicle at that speed have been.
    # the sensor distance to the road is the only factor affecting the speed calibration (frame rate is well known).
    # calibrating the argument of the acrsin() function is setting the maximum delay observed for endfire conditions.
    # v_sound/(fs * mic_spacing) = max delay in samples.  This is calibrated by adjusting the speed of sound or mic separation.
    if np.amin(p_row[i]) < 0:
        print('Error...Pointer less than buffer start')
    if (np.amax(p_row[i])) > num_vectors-1:
        print('Error....Pointer larger than buffer size')
    #print('i: ',i,'  min: ',np.amin(p_row[i]),'  max: ',np.amax(p_row[i]))
    if np.amin(n_row[i]) < 0:
        print('Error...Pointer less than buffer start')
    if (np.amax(n_row[i])) > num_vectors-1:
        print('Error....Pointer larger than buffer size')
    #print('i: ',i,'  min: ',np.amin(n_row[i]),'  max: ',np.amax(n_row[i]))
# check for valid numbers.  No index less than zero and no index larger than the buffer size (numVectors-1)
np.clip(p_row,0,num_vectors-1,out=p_row)
np.clip(n_row,0,num_vectors-1,out=n_row)

num_frames = 11             # number of frames of speed correlation results to save in circular buffer
num_frame_half = int((num_frames-1)/2)
frame_ptr = 0               # points to current frame in the speed result buffer
p_sum=np.zeros((num_frames,num_speeds),dtype=np.float32)                # allocate memory for overlap integral result positive speed
n_sum=np.zeros((num_frames,num_speeds),dtype=np.float32)                # allocate memory for overlap integral result negative speed
p_peak=np.zeros(num_frames,dtype=np.float32)                                 # storage for peak values in overlap sum table
n_peak=np.zeros(num_frames,dtype=np.float32)                                 # storage for peak values in overlap sum table
coeffs=np.zeros(num_frames,dtype=np.float32)                               # storage for matched filter coefficients
coeffs=np.divide([-1.0,-1.0,-1.0,0.0,0.0,6.0,0.0,0.0,-1.0,-1.0,-1.0],6.0)
detection_threshold = 0.7
p_found = 0
n_found = 0

b_img = np.zeros((1,1),dtype=np.float32)
o_img = np.zeros((1,1),dtype=np.float32)


speed_result = 0.0
peak_result = 0.0
result_ready = False



def find_peak(x, y):        # compute peak from quadratic interpolation curve
    A=(x[0]-x[1])*(x[0]-x[2])
    B=(x[1]-x[0])*(x[1]-x[2])
    C=(x[2]-x[0])*(x[2]-x[1])
    num=y[0]*(x[1]+x[2])*B*C + y[1]*(x[0]+x[2])*A*C + y[2]*(x[0]+x[1])*A*B
    den=y[0]*B*C + y[1]*A*C + y[2]*A*B
    return num/(2*den)
    

# initialize sqlite3 database if needed.
if not os.path.isfile(db_filename):
    #create an empty db file with speed table initialized
   con = sqlite3.connect(db_filename)
   db_cursor = con.cursor()
   db_cursor.execute('CREATE TABLE speed (DATE TEXT, SPEED REAL, PEAK REAL)')
   con.close()


# list ALSA devices and select the direct hardware port
for item in sd.query_devices():
    if (audio_input_selector in item['name']) and (item['max_input_channels']==2):
        print('Found ',item['name'])
        input_num=item['index']
        break
    else: 
        print('Error...No stereo audio input found.')
        sys.exit(1)

def save_results(speed, peak):
    global speed_result, peak_result, result_ready
    
    speed_result = speed
    peak_result = peak
    result_ready = True


def output_results():
    global speed_result, peak_result, result_ready    
    
    boresight_offset = timedelta(seconds=(float(num_vectors)/(2.0*frame_rate)))  # how long ago was the vehicle at boresight??
    date_str = str(datetime.now()-boresight_offset)
    speed_str = "{:+.1f}".format(speed_result)
    peak_str = "{:.2f}".format(peak_result)
    
    outstr = date_str + "  " + speed_str + " MPH  Peak: " + peak_str
    print(outstr)
    mqtt.single("/SoS/speed",abs(speed_result))
    mqtt.single("/SoS/velocity",speed_result)
    mqtt.single("/SoS/log",outstr)
    con = sqlite3.connect(db_filename)
    db_cursor = con.cursor()
    db_cursor.execute('INSERT INTO speed VALUES(?,?,?)',(date_str, float(speed_result), float(peak_result)))
    con.commit()
    con.close()
    result_ready = False



# set up interrupt handling routine for when audio capture has filled its buffer of samples

def audio_callback(indata, frames, time, status):  # parameters are local to callback
    global audio_samples
    global audio_DC
    global time_corr
    global buffer, ptr
    global num_speeds, speed
    global p_sum, n_sum, row, col, p_peak, n_peak, p_found, n_found, coeffs
    global frame_ptr, detection_threshold
    global p_overlap, n_overlap, b_img, o_img
    global speed_result, peak_result, result_ready
    
    if status:
        print('Status: ',status)     	# print error status if an error occurred.
    audio_DC = 0.9*audio_DC + 0.1*np.mean(indata,axis=0)     # compute a moving average value
    indata = indata - audio_DC     # remove DC content
#    print('#Frames: ',frames,'Time: ',time.inputBufferAdcTime,' Smax: ',indata[buf_size-1])

    # compute transforms
    left_spectrum = np.fft.fft(indata[:,0],n=buf_size,axis=0)
    right_spectrum = np.fft.fft(indata[:,1],n=buf_size,axis=0)
    cross_spectrum = left_spectrum * np.conjugate(right_spectrum)
    norm_spectrum = np.maximum(scale_factor * abs(cross_spectrum),1.0)  # normalize to whitening function spectrum but not smaller than 1
    corr_spectrum = scale_factor * (cross_spectrum/norm_spectrum)
    time_corr = np.fft.ifft(corr_spectrum).real
    time_corr = np.fft.fftshift(time_corr)          # due to normalizing, time correlation peaks will never be larger than 1
    #audio_samples = indata

    buffer[ptr] = time_corr     # store this vector into circular buffer

    for i in range(num_speeds):		# overlap calculation here
        p_sum[frame_ptr][i]=np.sum(buffer[(p_row[i]+ptr) % num_vectors, p_col])
        n_sum[frame_ptr][i]=np.sum(buffer[(n_row[i]+ptr) % num_vectors, n_col])
    p_overlap[(ptr+int(num_vectors/2))%num_vectors] = p_sum[frame_ptr]                        # save overlap result for debug display
    n_overlap[(ptr+int(num_vectors/2))%num_vectors] = n_sum[frame_ptr]

# publish correlation data using ZMQ
    socket.send_multipart([buffer[ptr][center-2*span:center+2*span],p_sum[frame_ptr],n_sum[frame_ptr]])

    # test for valid speed correlation peak
    p_peak=np.roll(p_peak,1)          # shift buffer so that element [0] is always the current value
    p_peak[0] = p_sum[frame_ptr].max()
    n_peak=np.roll(n_peak,1)
    n_peak[0] = n_sum[frame_ptr].max()

    # positive peak search
    peak_test=np.dot(p_peak,coeffs)           # perform matched FIR filter convolution to find peak
                    # we don't want to find two peaks right next to each other, so if a peak is found then skip ahead 5 frames
    if p_found > 0: 			# we are skipping frames if a peak was recently found (p_found > 0)
        p_found -= 1
    if (peak_test > detection_threshold) and (p_found <= 0):   # declare peak is found somewhere in frame buffer, go search for the peak
        j=np.argmax(p_peak)                                # j points _back in time_ to the frame which has the global peak
        k=(frame_ptr+num_frames-j) % num_frames       # k points to the frame with the global peak
        i=np.argmax(p_sum[k])       # i points to the speed in the speed buffer of the global peak
        p_speed_result=speed[i]
        if (i>0) and (i<num_speeds-1):
           p_speed_result=find_peak(speed[i-1:i+2],p_sum[k][i-1:i+2])       
        p_found = 5                                            #begin countdown to skip next few frames
        save_results(p_speed_result/0.447,p_peak[j])      # scale speed into MPH

    
    # negative peak search
    peak_test=np.dot(n_peak,coeffs)           # perform matched filter convolution to find peak
    if n_found > 0: 
        n_found -= 1
    if (peak_test > detection_threshold) and (n_found <= 0):   # declare peak is found somewhere in frame buffer, go search for the peak
        j=np.argmax(n_peak)                                # j points _back in time_ to the frame which has the global peak
        k=(frame_ptr+num_frames-j) % num_frames       # k points to the frame with the global peak
        i=np.argmax(n_sum[k])       # i points to the speed in the speed buffer of the global peak
        n_speed_result=speed[i]
        if (i>0) and (i<num_speeds-1):
           n_speed_result=find_peak(speed[i-1:i+2],n_sum[k][i-1:i+2])  # this lane is the other lane
        n_found = 5                                            #begin countdown to skip next few frames
        save_results(-n_speed_result/0.447,n_peak[j])      # scale speed into MPH


    
    if ptr == 0:     # if at beginning of buffer, then generate an image map of buffer
        b_img = buffer[:,center-2*span:center+2*span]
        b_max = b_img.max()
        b_min = b_img.min()
        b_img = (255.0*(b_img-b_min)/(1e-6+b_max-b_min))      # normalize scale from 0 to 255 for PNG brightness
   
    if ptr == int(num_vectors/2):            # save image of overlap calculation (delayed by half of buffer)
        o_img = np.concatenate((p_overlap,n_overlap),axis=1)
        o_min = o_img.min()
        o_max = o_img.max()
        o_img = 255.0*(o_img-o_min)/(1e-6+o_max-o_min)
        png.from_array(o_img.astype(np.int8),'L').save('overlap.png')   # save both files at the same time.
        png.from_array(b_img.astype(np.int8),'L').save('buffer.png')

    frame_ptr = (frame_ptr+1) % num_frames
    ptr = (ptr + 1) %  num_vectors            # wrap pointer around to beginning


    # context manager calls start() automatically
try:
    my_st = sd.InputStream(channels=2, device=input_num, blocksize=buf_size, samplerate=audio_sample_rate, callback=audio_callback)
        # do something which is non-blocking
    with my_st:
        print('Start...')
        while True:
            if result_ready:
                output_results()
            sd.sleep(10)    # sleep in ms
            #print(my_st.cpu_load)
        print('End.')
except:
    print('Error...quitting')
    sys.exit()

