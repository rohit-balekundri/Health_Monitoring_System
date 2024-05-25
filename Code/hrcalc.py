#Reference Link: Git Hub: https://github.com/rravivarman/RaspberryPi/tree/master/MAX30102

"""
The raw photoplethysmography (PPG) data are used to determine the heart rate (HR) and blood oxygen saturation level (SpO2) using the Python function calc_hr_and_spo2. 
Input parameters ir_data and red_data are NumPy arrays that, respectively, hold the infrared and red PPG signals.
The infrared PPG signal's DC mean is first calculated by the function, which then subtracts it from the signal. 
The noise is then removed by averaging the signal over four points. 
The threshold value is then calculated using the smoothed signal's mean and clipped between 30 and 60.
The peak detection algorithm is then used by the function to locate the troughs (minima) in the smoothed infrared PPG signal. 
It determines the peak interval sum, which is the total of the times between adjacent valleys. 
The heart rate is determined by taking the average peak interval's reciprocal and multiplying it by 60 to convert it from beats per second to beats per minute if there are at least two valleys. 
The heart rate is set to -999 if there are fewer than two valleys to denote that it was not possible to calculate.
The ratio between the AC component of the infrared PPG signal and the DC component of the red PPG signal is then used by the function to calculate the blood oxygen saturation level. 
The greatest DC components of the red and infrared signals are determined between each pair of subsequent valleys using the identical peak locations as before. 
The ratio is then calculated by subtracting the linear DC component from the raw signal to determine the AC component of each signal. 
In order to lessen the impact of any outliers, the function computes up to five ratios and takes the median value. 
The SpO2 is set to -999 to denote that it could not be calculated if there are less than two ratios.

"""
import numpy as np

# 25 samples per second (in algorithm.h)
SAMPLE_FREQ = 25

MA_SIZE = 4
# sampling frequency * 4 (in algorithm.h)
BUFFER_SIZE = 100


# this assumes ir_data and red_data as np.array
def calc_hr_and_spo2(ir_data, red_data):
    """
    By detecting  peaks of PPG cycle and corresponding AC/DC
    of red/infra-red signal, the an_ratio for the SPO2 is computed.
    """
   
    ir_mean = int(np.mean(ir_data))

  
    x = -1 * (np.array(ir_data) - ir_mean)

    # 4 point moving average
    # x is np.array with int values, so automatically casted to int
    for i in range(x.shape[0] - MA_SIZE):
        x[i] = np.sum(x[i:i+MA_SIZE]) / MA_SIZE

    # calculate threshold
    n_th = int(np.mean(x))
    n_th = 30 if n_th < 30 else n_th  # min allowed
    n_th = 60 if n_th > 60 else n_th  # max allowed

    ir_valley_locs, n_peaks = find_peaks(x, BUFFER_SIZE, n_th, 4, 15)
    
    peak_interval_sum = 0
    if n_peaks >= 2:
        for i in range(1, n_peaks):
            peak_interval_sum += (ir_valley_locs[i] - ir_valley_locs[i-1])
        peak_interval_sum = int(peak_interval_sum / (n_peaks - 1))
        hr = int(SAMPLE_FREQ * 60 / peak_interval_sum)
        hr_valid = True
    else:
        hr = -999  
        hr_valid = False

    # ---------spo2---------


    exact_ir_valley_locs_count = n_peaks

    
    for i in range(exact_ir_valley_locs_count):
        if ir_valley_locs[i] > BUFFER_SIZE:
            spo2 = -999  
            spo2_valid = False
            return hr, hr_valid, spo2, spo2_valid

    i_ratio_count = 0
    ratio = []

    
    red_dc_max_index = -1
    ir_dc_max_index = -1
    for k in range(exact_ir_valley_locs_count-1):
        red_dc_max = -16777216
        ir_dc_max = -16777216
        if ir_valley_locs[k+1] - ir_valley_locs[k] > 3:
            for i in range(ir_valley_locs[k], ir_valley_locs[k+1]):
                if ir_data[i] > ir_dc_max:
                    ir_dc_max = ir_data[i]
                    ir_dc_max_index = i
                if red_data[i] > red_dc_max:
                    red_dc_max = red_data[i]
                    red_dc_max_index = i

            red_ac = int((red_data[ir_valley_locs[k+1]] - red_data[ir_valley_locs[k]]) * (red_dc_max_index - ir_valley_locs[k]))
            red_ac = red_data[ir_valley_locs[k]] + int(red_ac / (ir_valley_locs[k+1] - ir_valley_locs[k]))
            red_ac = red_data[red_dc_max_index] - red_ac  # subtract linear DC components from raw

            ir_ac = int((ir_data[ir_valley_locs[k+1]] - ir_data[ir_valley_locs[k]]) * (ir_dc_max_index - ir_valley_locs[k]))
            ir_ac = ir_data[ir_valley_locs[k]] + int(ir_ac / (ir_valley_locs[k+1] - ir_valley_locs[k]))
            ir_ac = ir_data[ir_dc_max_index] - ir_ac  # subtract linear DC components from raw

            nume = red_ac * ir_dc_max
            denom = ir_ac * red_dc_max
            if (denom > 0 and i_ratio_count < 5) and nume != 0:
                
                ratio.append(int(((nume * 100) & 0xffffffff) / denom))
                i_ratio_count += 1

   
    ratio = sorted(ratio)  
    mid_index = int(i_ratio_count / 2)

    ratio_ave = 0
    if mid_index > 1:
        ratio_ave = int((ratio[mid_index-1] + ratio[mid_index])/2)
    else:
        if len(ratio) != 0:
            ratio_ave = ratio[mid_index]

    
    
    if ratio_ave > 2 and ratio_ave < 184:
        
        spo2 = -45.060 * (ratio_ave**2) / 10000.0 + 30.054 * ratio_ave / 100.0 + 94.845
        spo2_valid = True
    else:
        spo2 = -999
        spo2_valid = False
    
    return hr-20, hr_valid, spo2, spo2_valid


def find_peaks(x, size, min_height, min_dist, max_num):
   
    ir_valley_locs, n_peaks = find_peaks_above_min_height(x, size, min_height, max_num)
    ir_valley_locs, n_peaks = remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist)

    n_peaks = min([n_peaks, max_num])

    return ir_valley_locs, n_peaks


def find_peaks_above_min_height(x, size, min_height, max_num):

    i = 0
    n_peaks = 0
    ir_valley_locs = []  
    while i < size - 1:
        if x[i] > min_height and x[i] > x[i-1]:  
            n_width = 1
            
            while i + n_width < size - 1 and x[i] == x[i+n_width]:  
                n_width += 1
            if x[i] > x[i+n_width] and n_peaks < max_num:  
                
                ir_valley_locs.append(i)
                n_peaks += 1  
                i += n_width + 1
            else:
                i += n_width
        else:
            i += 1

    return ir_valley_locs, n_peaks


def remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist):
    
    sorted_indices = sorted(ir_valley_locs, key=lambda i: x[i])
    sorted_indices.reverse()

    i = -1
    while i < n_peaks:
        old_n_peaks = n_peaks
        n_peaks = i + 1
    
        j = i + 1
        while j < old_n_peaks:
            n_dist = (sorted_indices[j] - sorted_indices[i]) if i != -1 else (sorted_indices[j] + 1)  
            if n_dist > min_dist or n_dist < -1 * min_dist:
                sorted_indices[n_peaks] = sorted_indices[j]
                n_peaks += 1  
            j += 1
        i += 1

    sorted_indices[:n_peaks] = sorted(sorted_indices[:n_peaks])

    return sorted_indices, n_peaks
