# trip_classifier

# Instructions:
- first open "config.ini" file using a text editor (like sublime)
- assign values to each keys that are: 
  - input_path: path to a local directory where you have trip data
  - output_path: path to a local directory where you store output data. 
  - speed_bin_resolution: number of avg speed classifications
  - grade_bin_resolution: number of avg grade classifications
  - max_speed: maximum average speed in m/s. Trips that have an average speed higher than max_speed will be filtered out. In m/s.
  - min_speed: minimum average speed in m/s. Trips that have an average speed lower than min_speed will be filtered out.
  - max_grade: maximum average grade in rad. Trips that have an average grade higher than max_grade will be filtered out.
  - min_grade: minimum average grade in rad. Trips that have an average grade lower than min_grade will be filtered out.
  - should_create_new_copies: boolean flag (true/false) to copy and paste trip files in the output directory
- run "run_trip_clsf.py".
- done.

# Note: 
To see how the classifier works, look into the "get_cluster_index()" method in "run_trip_clsf.py". I documented how it works.
An output directory is named as "\<date\>\_\<time\>\_speed_bin\_\<resolution\>\_grade_bin\_\<resolution\>\_tot_trip\_\<num\>" and contains "cluster_index_map.csv" file that has avg speed and grade and cluster index for each trip. Trips that do not have any assigned cluster index in the csv file means "filtered out" as their avg speed/grade is out of the min-max range that you specified in the config file.
