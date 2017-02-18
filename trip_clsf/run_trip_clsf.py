# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 22:21:26 2017

@author: Sangjae Bae
"""
from os import listdir, getcwd, makedirs
from os.path import isfile, join, exists
import time
import ConfigParser as cp
import pandas as pd
import math
import csv
import datetime
import shutil

#%%============================ Methods ========================================#

# cluster trips with avg speed and grade
def get_each_bin_range(size_bin_speed, max_bin_speed, size_bin_grade, max_bin_grade, min_bin_speed = 0, min_bin_grade = -0.5):
    '''
    return range of each bin

    '''

    ds = (max_bin_speed - min_bin_speed)/size_bin_speed
    dg = (max_bin_grade - min_bin_grade)/size_bin_grade
    return ds, dg


def get_cluster_index(avg_speed, avg_grade, ds, dg, max_bin_speed = 35, max_bin_grade = 0.5, min_bin_speed = 0, min_bin_grade = -0.5):
    '''
    get the cluster number for given average speed and average grade
    
    how it works:
    - with given resolutions of speed bins and grade bins, imagine that you 
      have a 2D matrix with rows for avg speed and columns for avg grade. Then 
      the clusters are numbered from row to column, i.e., 
        
      cluster_index = (row_number - 1)*(column_length) + column_number
              
      For instance, when we have 20 bins for speed and 20 bins for grade, which
      correpond to 20 rows and 20 columns, respectively, the cluster 
      at (1,3) in the matrix is indexed as 3, the cluster at (2,1) in the 
      matrix is indexed as 21.

    '''

    # get row index    
    row_num = math.ceil((avg_speed-min_bin_speed)/ds)
    if(row_num <= 0):
        raise ValueError('row index cannot be non positive!')
    # get column index
    col_num = math.ceil((avg_grade-min_bin_grade)/dg)
    if(col_num <= 0):
        raise ValueError('column index cannot be non positive!')
    # handle exceptions
    if(avg_speed > max_bin_speed):
        raise ValueError('average speed cannot exceed the maximum speed!')
    if(avg_grade > max_bin_grade):
        raise ValueError('average grade cannot exceed the maximum grade!')
    # return cluster index        
    return int((row_num-1)*((max_bin_grade-min_bin_grade)/dg)+col_num)

#%%============================ Main script ====================================#
print('Loading configurations...')
time_start = time.clock()

# Load config file
config = cp.ConfigParser()
dir_path = getcwd()
config.read(join(dir_path,'config.ini'))

# Initialize config
max_bin_speed = float(config.get('configs','max_speed'))
max_bin_grade = float(config.get('configs','max_grade'))
min_bin_speed = float(config.get('configs','min_speed'))
min_bin_grade = float(config.get('configs','min_grade'))
size_bin_speed = int(config.get('configs','speed_bin_resolution'))
size_bin_grade = int(config.get('configs','grade_bin_resolution'))
trip_dir_path = config.get('configs','input_path')
output_dir_path = config.get('configs','ouput_path')
should_create_new_copies = bool(config.get('configs','should_create_new_copies'))
ds, dg = get_each_bin_range(size_bin_speed, max_bin_speed, size_bin_grade, max_bin_grade, 
                           min_bin_speed = min_bin_speed, min_bin_grade = min_bin_grade)

file_name_list = [f for f in listdir(trip_dir_path) if isfile(join(trip_dir_path, f))]
file_name_list = file_name_list[1:-1]
cluster_index_arr = [0]*len(file_name_list)
avg_speed_arr = [0]*len(file_name_list)
avg_grade_arr = [0]*len(file_name_list)
cluster_index_dict = {}

#%%-------- For loop from here
print('Classifying...')
for i,f in enumerate(file_name_list):
    # Read csv file
    df = pd.read_csv(join(trip_dir_path,f))
    speed_col = df.speed
    alt_col = df.altitude
    
    # Get average speed in m/s
    avg_speed = df.speed.mean(numeric_only=False)

    # Get average grade in rad
    grade_arr_in_rad = [math.atan(y/x) for x,y in zip(speed_col[1:-1],alt_col.diff(periods=1)[1:-1]) if not x == 0]
    
    # Get cluster index    
    if(len(grade_arr_in_rad) == 0):
        cluster_index = None
    else:
        avg_grade = sum(grade_arr_in_rad)/len(grade_arr_in_rad)
        if(avg_grade > max_bin_grade or avg_grade < min_bin_grade or avg_speed > max_bin_speed or avg_speed < min_bin_speed):
            cluster_index = None
        else:
            cluster_index = get_cluster_index(avg_speed, avg_grade, ds, dg, 
                                              max_bin_speed=max_bin_speed, max_bin_grade=max_bin_grade, 
                                              min_bin_speed=min_bin_speed, min_bin_grade=min_bin_grade)
    
    # Store the cluter index in array
    cluster_index_arr[i] = cluster_index
    avg_speed_arr[i] = avg_speed
    avg_grade_arr[i] = avg_grade
    cluster_index_dict[f] = cluster_index

#%%---------- copy and past trip files in the new output directory

sub_dir_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_")+'speed_bin_'+str(size_bin_speed) + '_grade_bin_' +str(size_bin_grade) + '_tot_trip_' + str(len(file_name_list))
if not (exists(join(output_dir_path, sub_dir_name))):
    makedirs(join(output_dir_path, sub_dir_name))
        
with open(join(output_dir_path, sub_dir_name,'cluster_index_map.csv'), 'wb') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['trip_file','cluster_index_tot_'+str(size_bin_speed*size_bin_grade),'avg_speed_in_m_per_s','avg_grade_in_rad'])
    for key, value, avg_speed, avg_grade in zip(list(cluster_index_dict.keys()), list(cluster_index_dict.values()), avg_speed_arr, avg_grade_arr):
       writer.writerow([key, value, avg_speed, avg_grade])

if(should_create_new_copies):    
    # create the cluster directories in the sub directory
    for i in range(1,size_bin_speed*size_bin_grade+1):
        makedirs(join(output_dir_path, sub_dir_name, str(i)))

    # copy the files and past in the associated directories
    for f in file_name_list:    
        srcfile = join(trip_dir_path, f)
        dstdir = join(output_dir_path, sub_dir_name, str(cluster_index_dict[f]))
        shutil.copy(srcfile, dstdir)
else:
    with open(join(output_dir_path, sub_dir_name,'cluster_index_map.csv'), 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['trip_file','cluster_index_tot_'+str(size_bin_speed*size_bin_grade),'avg_speed_in_m_per_s','avg_grade_in_rad'])
        for key, value, avg_speed, avg_grade in zip(list(cluster_index_dict.keys()), list(cluster_index_dict.values()), avg_speed_arr, avg_grade_arr):
           writer.writerow([key, value, avg_speed, avg_grade])

time_elapsed = (time.clock() - time_start)
print('\nDONE in '+str(time_elapsed)+' seconds')