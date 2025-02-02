#THE VERSION WHERE I ACCOUNT FOR MANY FEED-FEED VARIABLES

import h5py
import numpy as np
import itertools as itr
import tools


# --- READ jk_list ---

#(! keep test variables after control variables in jk_list)
# marked with 3 - control variables - produce all the different combinations of these 
# marked with 2 - test variables - look at only one of these, while the rest is co-added - can be found in the map file
# marked with extra 1 - the variable used for feed-feed cross spectra

def read_jk(filename):
   print ('STAGE 1/4: Reading the list of variables associated with the map.')
   jk_file = open(filename, 'r')
   all_lines = jk_file.readlines()
   jk_file.close()
   all_lines = all_lines[2:] #skip the first two lines (number of different jk and accr)
   control_variables = [] #marked with 3
   test_variables = [] #marked with 2
   feed_feed_variables = [] #extra 1
   all_variables = []
   for line in all_lines:
      split_line = line.split()
      variable = split_line[0]
      number = split_line[1]
      if len(split_line) > 2:
         extra = split_line[2]
      if len(split_line) < 2 or len(split_line) == 2:
         extra = '#'
      all_variables.append(variable)

      if number == '3':
         control_variables.append(variable)
        
      if number == '2':
         test_variables.append(variable)
         
      if extra == '1':
         feed_feed_variables.append(variable) 

   #find all feed-feed variables that are also test variables or control variables
   feed_and_test = []
   feed_and_control = [] 
   for variable in all_variables:
      if variable in test_variables and variable in feed_feed_variables:
         feed_and_test.append(variable)
      if variable in feed_feed_variables and variable in control_variables:
         feed_and_control.append(variable)
 
   return control_variables, test_variables, feed_feed_variables, all_variables, feed_and_test, feed_and_control

def read_map(mappath, field, control_variables, test_variables, feed_feed_variables, all_variables, feed_and_test, feed_and_control):
   print ('STAGE 2/4: Splitting the map into subsets with different split combinations.')
   input_map = h5py.File(mappath, 'r')
   
   outdir = mappath.split("/")[-1].split(".")[0]

   x = np.array(input_map['x'][:]) #common part for all maps
   y = np.array(input_map['y'][:]) #common part for all maps
   multisplits = input_map['multisplits']
   maps_created = []
   if len(feed_and_test) != 0: #if some test variables are simultaneously feed-feed variables
      for test_variable in feed_and_test:
     
            map_split = np.array(multisplits['map_' + test_variable][:])
            rms_split = np.array(multisplits['rms_' + test_variable][:])
            shp = map_split.shape
            how_many_twos = len(control_variables) + 1 #how many parts to reshape the map with respect to splits
            new_shape = []
            for i in range(how_many_twos):
               new_shape.append(2) #because we split in 2 - needs to be changed if more splits are implemented
            new_shape.append(shp[1]) #feed
            new_shape.append(shp[2]) #sideband
            new_shape.append(shp[3]) #freq
            new_shape.append(shp[4]) #x
            new_shape.append(shp[5]) #y
            map_split = map_split.reshape(new_shape)
            rms_split = rms_split.reshape(new_shape)
            split_names = [] #collect the names of the spits in the correct order for the new shape
            split_names.append(test_variable)
            for i in range(how_many_twos-1):
               split_names.append(control_variables[-1-i])
             
            how_many_to_combine = len(split_names) -1 #all control variables
            all_different_possibilities = list(itr.product(range(2), repeat=how_many_to_combine)) #find all the combinations of 'how_many_to_combine' 0s and 1s  
            index_of_ff_variable = 0
   
            all_axes_to_combine = list(range(0,how_many_to_combine+1))
            
            all_axes_to_combine.remove(index_of_ff_variable) #all axes for different combinations of splits, include both splits for the feed-feed variable
      
            slc = [slice(None)]*len(new_shape) #includes all elements
      
            for i in range(len(all_different_possibilities)): #this many maps will be created
               for_naming = [] #identify which combination of splits the current map is using
                
               for j in range(how_many_to_combine):
                  axis_index = all_axes_to_combine[j]
                  slc[axis_index] = all_different_possibilities[i][j] #choose 0 or 1 for this split
                  for_naming.append(split_names[axis_index])
                  for_naming.append(all_different_possibilities[i][j])
                 
               my_map = map_split[tuple(slc)] #slice the map for the current combination of splits
               my_rms = rms_split[tuple(slc)] #slice the rms-map for the current combination of splits
               name = field + '_' + 'map' + '_' + test_variable
               for k in range(len(for_naming)):
                  name += '_'
                  name += str(for_naming[k])
               name += '.h5'
               maps_created.append(name) #add the name of the current map to the list
               print ('Creating HDF5 file for the map ' + name + '.')
               tools.ensure_dir_exists('split_maps/' + outdir)
               outname = 'split_maps/' + outdir + '/' + name
               #outname = 'split_maps/' + name

               f = h5py.File(outname, 'w') #create HDF5 file with the sliced map
               f.create_dataset('x', data=x)
               f.create_dataset('y', data=y)
               f.create_dataset('/jackknives/map_' + test_variable, data=my_map)
               f.create_dataset('/jackknives/rms_' + test_variable, data=my_rms)
               f.close()

   if len(feed_and_control) != 0: #if some feed-feed variables are control variables
      for ff_variable in feed_and_control:
         for test_variable in test_variables:
            map_split = np.array(multisplits['map_' + test_variable][:])
            rms_split = np.array(multisplits['rms_' + test_variable][:])
            shp = map_split.shape
            how_many_twos = len(all_variables) - len(test_variables) + 1 #how to reshape the map with respect to splits
            new_shape = []
            for i in range(how_many_twos):
               new_shape.append(2)
            new_shape.append(shp[1]) #feed
            new_shape.append(shp[2]) #sideband
            new_shape.append(shp[3]) #freq
            new_shape.append(shp[4]) #x
            new_shape.append(shp[5]) #y
            map_split = map_split.reshape(new_shape)
            rms_split = rms_split.reshape(new_shape)
            split_names = [] #collect the names of the spits in the correct order for the new shape
            split_names.append(test_variable)
            for i in range(how_many_twos-1):
               split_names.append(all_variables[-len(test_variables)-1-i])
             
            how_many_to_combine = len(split_names) -1 #test variable + all control variables, except for the ff_variable
            all_different_possibilities = list(itr.product(range(2), repeat=how_many_to_combine)) #find all the combinations of 'how_many_to_combine' 0s and 1s  
            index_of_ff_variable = split_names.index(ff_variable)
   
            all_axes_to_combine = list(range(0,how_many_to_combine+1))
            
            all_axes_to_combine.remove(index_of_ff_variable) #all axes for different combinations of splits, include both splits for the feed-feed variable
      
            slc = [slice(None)]*len(new_shape) #includes all elements
      
            for i in range(len(all_different_possibilities)): #this many maps will be created
               for_naming = [] #identify which combination of splits the current map is using
                
               for j in range(how_many_to_combine):
                  axis_index = all_axes_to_combine[j]
                  slc[axis_index] = all_different_possibilities[i][j] #choose 0 or 1 for this split
                  for_naming.append(split_names[axis_index])
                  for_naming.append(all_different_possibilities[i][j])
                 
               my_map = map_split[tuple(slc)] #slice the map for the current combination of splits
               my_rms = rms_split[tuple(slc)] #slice the rms-map for the current combination of splits
               name = field + '_' + 'map' + '_' + ff_variable
               for k in range(len(for_naming)):
                  name += '_'
                  name += str(for_naming[k])
               name += '.h5'
               maps_created.append(name) #add the name of the current map to the list
               print ('Creating HDF5 file for the map ' + name + '.')
               tools.ensure_dir_exists('split_maps/' + outdir)
               #outname = 'split_maps/' + name
               outname = 'split_maps/' + outdir + '/' + name

               f = h5py.File(outname, 'w') #create HDF5 file with the sliced map
               f.create_dataset('x', data=x)
               f.create_dataset('y', data=y)
               f.create_dataset('/jackknives/map_' + ff_variable, data=my_map)
               f.create_dataset('/jackknives/rms_' + ff_variable, data=my_rms)
               f.close()
   
   return maps_created

def read_map_created(mapfile):
   with h5py.File(mapfile, mode="r") as my_file:
         map_old = np.array(my_file['/jackknives/map_elev'][:])
         rms_old = np.array(my_file['/jackknives/rms_elev'][:])
   return map_old, rms_old
     
def write_map_created(mapfile1, new_map, new_rms, test_variable, cesc, field):
   outdir = mappath.split("/")[-1].split(".")[0]

   with h5py.File(mapfile1, mode="r") as my_file1:
         x = np.array(my_file1['x'][:])
         y = np.array(my_file1['y'][:])

   outname1 = field + '_map_elev_' + test_variable + '_subtr_cesc_' + cesc +'.h5'
   print ('Creating the file ' + outname1)
   tools.ensure_dir_exists('split_maps/' + outdir)

   outname = 'split_maps/' + outdir + '/' + outname1
   #outname = 'split_maps/' + outname1

   f = h5py.File(outname, 'w') #create HDF5 file with the sliced map
   f.create_dataset('x', data=x)
   f.create_dataset('y', data=y)
   f.create_dataset('/jackknives/map_elev', data=new_map)
   f.create_dataset('/jackknives/rms_elev', data=new_rms)
   f.close()
   return outname1

def null_test_subtract(maps_created, test_variables, field):
   print ('Subtracting test-variable maps for the null-tests.')
   '''
   We want to subract split-maps (split according to test variables) for both cesc = 0 and cesc = 1 and then create new map-files for the FPXS.
   This sequence: ['co6_map_elev_ambt_0_cesc_0.h5', 'co6_map_elev_ambt_0_cesc_1.h5', 'co6_map_elev_ambt_1_cesc_0.h5',  
   'co6_map_elev_ambt_1_cesc_1.h5'] is repeating for different test variables.
   We want: 'co6_map_elev_ambt_1_cesc_0.h5 - co6_map_elev_ambt_0_cesc_0.h5' and call it 'co6_map_elev_ambt_subtr_cesc_0.h5'.
   '''
   number_of_maps = len(maps_created) 
   mapfiles = []
   new_subtracted_maps = []
   for i in range(number_of_maps):
      mapfiles.append('split_maps/' + maps_created[i])
   for i in range(len(test_variables)):
      test_variable = test_variables[i]
      mapfile1 = mapfiles[i*4] #test_variable = 0, cesc = 0
      mapfile2 = mapfiles[i*4+2] #test_variable = 1, cesc = 0
      mapfile3 = mapfiles[i*4+1] #test_variable = 0, cesc = 1
      mapfile4 = mapfiles[i*4+3] #test_variable = 1, cesc = 1
      map1, rms1 = read_map_created(mapfile1)
      map2, rms2 = read_map_created(mapfile2)
      map3, rms3 = read_map_created(mapfile3)
      map4, rms4 = read_map_created(mapfile4)
      map12 = map1-map2
      rms12 = np.sqrt(rms1**2 + rms2**2)
      map34 = map3-map4
      rms34 = np.sqrt(rms3**2 + rms4**2)
      new_map12 = write_map_created(mapfile1, map12, rms12, test_variable,'0',field)
      new_map34 = write_map_created(mapfile1, map34, rms34, test_variable,'1',field)
      new_subtracted_maps.append(new_map12)
      new_subtracted_maps.append(new_map34)
   print (new_subtracted_maps)
   return new_subtracted_maps

def read_field_jklist(mappath):
   map_name = mappath.rpartition('/')[-1] #get rid of the path, leave only the name of the map
   map_name = map_name.rpartition('.')[0] #get rid of the ".h5" part
   field_name = map_name.split('_')[0]
   last_part = map_name.split('_')[-1]
   jk_list = '/mn/stornext/d16/cmbco/comap/protodir/auxiliary/jk_list_' + last_part + '.txt'
   print ('Field:', field_name)
   print ('List of split-variables:', jk_list)
   return field_name, jk_list, map_name

'''
mappath = '/mn/stornext/d16/cmbco/comap/protodir/maps/co6_map_null.h5'
field_name, jk_list, map_name = read_field_jklist(mappath)
control_variables, test_variables, feed_feed_variables, all_variables, feed_and_test, feed_and_control = read_jk(jk_list)
#['ambt', 'wind', 'wint', 'rise', 'half', 'odde', 'fpol', 'dayn']
maps_created = read_map(mappath,field_name, control_variables, test_variables, feed_feed_variables, all_variables, feed_and_test, feed_and_control)
new_subtracted_maps = null_test_subtract(maps_created, test_variables, field_name)
'''

'''
['co6_map_elev_ambt_0_cesc_0.h5', 'co6_map_elev_ambt_0_cesc_1.h5', 'co6_map_elev_ambt_1_cesc_0.h5', 'co6_map_elev_ambt_1_cesc_1.h5', 'co6_map_elev_wind_0_cesc_0.h5', 'co6_map_elev_wind_0_cesc_1.h5', 'co6_map_elev_wind_1_cesc_0.h5', 'co6_map_elev_wind_1_cesc_1.h5', 'co6_map_elev_wint_0_cesc_0.h5', 'co6_map_elev_wint_0_cesc_1.h5', 'co6_map_elev_wint_1_cesc_0.h5', 'co6_map_elev_wint_1_cesc_1.h5', 'co6_map_elev_rise_0_cesc_0.h5', 'co6_map_elev_rise_0_cesc_1.h5', 'co6_map_elev_rise_1_cesc_0.h5', 'co6_map_elev_rise_1_cesc_1.h5', 'co6_map_elev_half_0_cesc_0.h5', 'co6_map_elev_half_0_cesc_1.h5', 'co6_map_elev_half_1_cesc_0.h5', 'co6_map_elev_half_1_cesc_1.h5', 'co6_map_elev_odde_0_cesc_0.h5', 'co6_map_elev_odde_0_cesc_1.h5', 'co6_map_elev_odde_1_cesc_0.h5', 'co6_map_elev_odde_1_cesc_1.h5', 'co6_map_elev_fpol_0_cesc_0.h5', 'co6_map_elev_fpol_0_cesc_1.h5', 'co6_map_elev_fpol_1_cesc_0.h5', 'co6_map_elev_fpol_1_cesc_1.h5', 'co6_map_elev_dayn_0_cesc_0.h5', 'co6_map_elev_dayn_0_cesc_1.h5', 'co6_map_elev_dayn_1_cesc_0.h5', 'co6_map_elev_dayn_1_cesc_1.h5']
'''



'''
EXAMPLES:

--jk_list:
6        # number of different jack-knives (including acceptlist)
accr     # accept/reject (reject=0)
snup     3 1
cesc     3 #
elev     2 #
ambt     2 #
half     2 # sad
--maps:
['co2_map_snup_elev_0_cesc_0.h5', 'co2_map_snup_elev_0_cesc_1.h5', 'co2_map_snup_elev_1_cesc_0.h5', 'co2_map_snup_elev_1_cesc_1.h5', 'co2_map_snup_ambt_0_cesc_0.h5', 'co2_map_snup_ambt_0_cesc_1.h5', 'co2_map_snup_ambt_1_cesc_0.h5', 'co2_map_snup_ambt_1_cesc_1.h5', 'co2_map_snup_half_0_cesc_0.h5', 'co2_map_snup_half_0_cesc_1.h5', 'co2_map_snup_half_1_cesc_0.h5', 'co2_map_snup_half_1_cesc_1.h5']


--jk_list_signal.txt:
4        # number of different jack-knives (including acceptlist)
accr     # accept/reject (reject=0)
cesc     3 #
elev     2 1 #
dayn     2 1
--maps:
['co2_map_elev_cesc_0.h5', 'co2_map_elev_cesc_1.h5', 'co2_map_dayn_cesc_0.h5', 'co2_map_dayn_cesc_1.h5']

--jk_list_signal.txt, new file:
9        # number of different jack-knives (including acceptlist)
accr     # accept/reject (reject=0)
cesc     3 #
elev     2 1 #
dayn     2 1
sidr     2 1
ambt     2 1
wind     2 1
wint     2 1
rise     2 1


--jk_list_null.txt, for the null test
11	 # number of different jack-knives (including acceptlist)
accr     # accept/reject (reject=0)
cesc     3 #
elev     3 1 #
ambt     2
wind     2
wint     2
rise     2
half     2
odde     2
fpol     2
dayn     2

'''


