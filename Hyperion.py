### potential alternative names--Pontifex? Spinifex?


import glob
import math
import copy
import numpy as np 
import ehtim as eh
import matplotlib.pyplot as plt 
from scipy.signal import argrelextrema
from matplotlib.patches import Ellipse
from scipy.interpolate import UnivariateSpline 

# Global variables ##########################
VERBOSE_FLAG = False
valve = None



# Classes ###################################


# Functions #################################
def print_verbose(message):
    """
        Prints a message if the verbose flag is set. To 
        set VERBOSE_FLAG to true, use SET_VERBOSE()
        Args:
            message: message to print if verbose flag is on
    """
    global VERBOSE_FLAG
    if VERBOSE_FLAG:
        print message

def SET_VERBOSE(flag=False):
    """
        Function to either pass a specific flag to VERBOSE_FLAG
        or to just switch the state
    """
    global VERBOSE_FLAG
    if flag:
        VERBOSE_FLAG = flag
        return 1
    if not flag:
        VERBOSE_FLAG = not VERBOSE_FLAG

def get_center_from_matrix(vec, thresh):
    """ 
        given a vector and a threshold, return the center of the matrix
        Args:
            vec:    one dimensional vector of intensities
            thresh: percentage of flux to mask
        Returns:
            center: tuple containing xy coordinate of center
    """
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    (x,y) = np.nonzero(vec > np.max(vec)*float(thresh))
    center = (int(np.mean(x)), int(np.mean(y)))
    print_verbose(center)
    return center

def get_outer_circle(image, thresh=0.0):
    """ 
        function to get the center point and arms of
        the black hole ring
        Args:
            image:  an Image object from Andrew's library
            thresh: percentage below which to mask flux (default=0%)
        Returns:
            (cx, cy, rx, ry): the center coordinates and radii
    """

    ''' sanitize input '''
    thresh = float(thresh)
    print_verbose("Threshold set to {0}".format(thresh))
    im = image
    

    ''' get center of image '''
    (CENTER_X, CENTER_Y) = get_center_from_matrix(im.imvec, thresh)
    print_verbose("Got center as: x={0}, y={1}".format(CENTER_X, CENTER_Y))

    ''' get corresponding row and column from imvec 
        based on the center parsed above
    '''
    vec = im.imvec

    # reshape the image vector based on the squareroot of the length
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    print_verbose("Vec shape now: {0}".format(vec.shape))

    # extract the row and column using splicing
    center_row = vec[CENTER_X,:]
    center_col = vec[:,CENTER_Y]
    print_verbose("row")
    print_verbose(center_row)
    print_verbose("col")
    print_verbose(center_col)

    ''' get peaks of intensity distribution ''' 
    for i in range(0,98):
        try:
            row_peaks = argrelextrema(
                center_row, 
                np.greater, 
                order=100-i
            )
            if len(row_peaks[0]) != 2:
                continue
            a = row_peaks[0][1]
        except IndexError:
            continue
        break

    # get the peaks from the array
    row_peaks = row_peaks[0][row_peaks[0] > 0]

    # get column peaks
    for i in range(0,98):
        try:
            col_peaks = argrelextrema(center_col, np.greater, order=100-i)
            a = col_peaks[0][1]
        except IndexError:
            continue
        break

    return (CENTER_X, CENTER_Y, float(row_peaks[-1]-row_peaks[0])/2, (float(col_peaks[0][-1]-col_peaks[0][0])/2))


def get_inner_circle(image, rx, ry, thresh=0.0):
    """ 
        function to get the center point and arms of
        the INNER black hole ring
        Args:
            image:  an Image object from Andrew's library
            thresh: percentage below which to mask flux (default=0%)
        Returns:
            (cx, cy, rx, ry): the center coordinates and radii
    """

    ''' sanitize input '''
    thresh = float(thresh)
    print_verbose("Threshold set to {0}".format(thresh))
    im = image
    

    ''' get center of image '''
    (CENTER_X, CENTER_Y) = get_center_from_matrix(im.imvec, thresh)
    print_verbose("Got center as: x={0}, y={1}".format(CENTER_X, CENTER_Y))

    ''' get corresponding row and column from imvec 
        based on the center parsed above
    '''
    vec = im.imvec

    # reshape the image vector based on the squareroot of the length
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    print_verbose("Vec shape now: {0}".format(vec.shape))

    # extract the row and column using splicing
    center_row = vec[CENTER_X,:]
    center_col = vec[:,CENTER_Y]
    col_peaks = 0

    for i in range(0,98):
        try:
            col_peaks = argrelextrema(
                center_col, 
                np.less, 
                order=100-i
            )
            a=  col_peaks[0][1]
        except IndexError:
            continue
        break

    col_peak_val = np.asarray([center_col[i] for i in col_peaks[0]])

    small_idx = col_peak_val.argsort()[:1]
    # print "smidx", small_idx
    print col_peaks
    inner_cy = col_peaks[0][small_idx[0]]
    # print "innercy", inner_cy
    center_row = vec[:,inner_cy]

    # print center_row
    for i in range(0,98):
        try:
            row_peaks = argrelextrema(center_row, np.less, order=100-i)
            a = i, row_peaks[0][0]
        except IndexError:
            if i==97:
                row_peaks = np.asarray([[im.xdim/2]])
            continue

        break
    # print 'row peaks', row_peaks
    row_peak_val = np.asarray([center_row[i] for i in row_peaks[0]])
    small_idx = row_peak_val.argsort()[:1]
    # print len(small_idx)
    inner_cx = row_peaks[0][small_idx[0]]
    # print "cx", inner_cx

    radiusy = 0.3*ry
    radiusx = 0.3*rx

    return (inner_cx, inner_cy, radiusx, radiusy)

def get_horizontal_peaks(image, thresh=0.0, get_center=True, angle=0, flux_thresh = 0.0, ring_thresh=0.0, return_error=False):
    """ 
        get a single horizontal peak flux from 
        two sides of a centerpoint

        !!! IF YOU WANT get_center TO BE ANYTHING BUT TRUE
            YOU MUST SET IT EQUAL TO AN (X,Y) TUPLE!
        !!!
    """
    ''' sanitize input '''
    thresh = float(thresh)
    print_verbose("Threshold set to {0}".format(thresh))
    im = image
    im = im.rotate(angle)

    ''' get center of image if get_center is flagged '''
    if get_center ==  True:    
        (CENTER_X, CENTER_Y) = get_center_from_matrix(im.imvec, thresh)
        print_verbose("Got center as: x={0}, y={1}".format(CENTER_X, CENTER_Y))
    else:
        (CENTER_X, CENTER_Y) = get_center

    ''' get corresponding row and column from imvec 
        based on the center parsed above
    '''
    vec = im.imvec

    ''' if element is below threshold, set it to threshold '''
    # sub_threshold_indices = vec < (flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # sub_threshold_indices = vec > (.9-flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # # vec = vec[vec > flux_thresh*np.max(vec)]
 
    # reshape the image vector based on the squareroot of the length
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    print_verbose("Vec shape now: {0}".format(vec.shape))

    # extract the row and column using splicing
    center_row = vec[CENTER_X,:]
    center_col = vec[:,CENTER_Y]
    print_verbose("row")
    print_verbose(center_row)
    print_verbose("col")
    print_verbose(center_col)

    i_spl = UnivariateSpline(range(len(center_row)),center_row,s=0,k=4)
    i_spl_2d = i_spl.derivative(n=1)
    new_i = np.asarray([i_spl_2d(x) for x in range(len(center_row))])
    ''' get peaks of intensity distribution ''' 
    for i in range(0,98):
        try:
            row_peaks = argrelextrema(
                center_row, 
                np.greater, 
                order=100-i
            )
            if len(row_peaks[0]) != 2:
                continue
        except IndexError:
            continue
        break

    def sub_thresh(a):
        return a-(ring_thresh*np.max(center_row))
    center_row = map(sub_thresh, center_row)

    ''' get inflection points of intensity distribution '''
    # plt.plot(center_row)
    # plt.title('Intensity distribution by position along cross-section')
    # plt.xlabel('Position (pixels)')
    # plt.ylabel('Intensity')
    # # # plt.plot(new_i)
    plt.plot(center_row)
    # plt.savefig("_WEIGHTED{0}.png".format(str(float((angle/math.pi)*35.))))
    # plt.clf()
    # plt.show()
    # print new_i
    ips = get_inflection_points(new_i, CENTER_X, image)


    # get the peaks from the array
    row_peaks = row_peaks[0][row_peaks[0] > 0]

    if return_error:
        try:
            error = find_fwhm(row_peaks[0], row_peaks[1], center_row)
        except:
            error = 0
        return convert_coordinates(row_peaks[0], row_peaks[1], CENTER_Y, angle, CENTER_X, CENTER_Y), error

    ''' convert coordinates using angle and return '''
    return convert_coordinates(row_peaks[0], row_peaks[1], CENTER_Y, angle, CENTER_X, CENTER_Y)



def get_center_row(image, thresh=0.0, get_center=True, angle=0, flux_thresh = 0.0, ring_thresh=0.0, return_error=False):
    """ 
        get a single horizontal peak flux from 
        two sides of a centerpoint

        !!! IF YOU WANT get_center TO BE ANYTHING BUT TRUE
            YOU MUST SET IT EQUAL TO AN (X,Y) TUPLE!
        !!!
    """
    ''' sanitize input '''
    thresh = float(thresh)
    print_verbose("Threshold set to {0}".format(thresh))
    im = image
    im = im.rotate(angle)

    ''' get center of image if get_center is flagged '''
    if get_center ==  True:    
        (CENTER_X, CENTER_Y) = get_center_from_matrix(im.imvec, thresh)
        print_verbose("Got center as: x={0}, y={1}".format(CENTER_X, CENTER_Y))
    else:
        (CENTER_X, CENTER_Y) = get_center

    ''' get corresponding row and column from imvec 
        based on the center parsed above
    '''
    vec = im.imvec

    ''' if element is below threshold, set it to threshold '''
    # sub_threshold_indices = vec < (flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # sub_threshold_indices = vec > (.9-flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # # vec = vec[vec > flux_thresh*np.max(vec)]
 
    # reshape the image vector based on the squareroot of the length
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    print_verbose("Vec shape now: {0}".format(vec.shape))

    # extract the row and column using splicing
    center_row = vec[CENTER_X,:]
    return center_row


def convert_coordinates(x1, x2, y1, theta, cx, cy):
    hx2 = x2-cx
    hx1 = x1-cx

    x1 = x1-(x1+x2)/2.
    x2 = x2-(x1+x2)/2.
    # print x1, x2
    hypotenuse = math.sqrt(x1**2 + y1**2)
    x1prime = hx1*math.cos(theta) + 1
    x2prime = hx2*math.cos(theta) + 1
    y1prime = hx1*math.sin(theta) - 1 
    y2prime = hx2*math.sin(theta) - 1
    return ([x1prime+cx, x2prime+cx], [y1prime+cy, y2prime+cy])


def get_inflection_points(vector, cx, im):
    (cx, cy, rx, ry) = get_outer_circle(im)
    bound1 = cx+rx
    bound2 = cx-rx
    bound3 = cx+(0.3*rx)
    bound4 = cx-(0.3*rx)
    signs = []
    inflection_point_indices = []
    for elem in vector:
        sign = abs(elem)/elem
        signs.append(sign)
    for i, sign in enumerate(signs):
        if i != len(signs)-1:
            if i > cx and i < bound1:
                if sign != signs[i-1]:
                    if i > 5 and i < 95:
                        inflection_point_indices.append(i)
            elif i <= cx and i > bound2:
                if sign != signs[i-1]:
                    if i > 5 and i < 95:
                        inflection_point_indices.append(i)
            # if sign != signs[i-1]:
            #     inflection_point_indices.append(i)
    # print inflection_point_indices

    max_pair_len = 0
    for i, elem in enumerate(inflection_point_indices):
        if i != len(inflection_point_indices)-1:
            diff = inflection_point_indices[i+1] - elem
            if diff > max_pair_len:
                max_pair_len = diff
                max_pair = [copy.copy(inflection_point_indices[i]), copy.copy(inflection_point_indices[i+1])]
    # if len(inflection_point_indices) > 3:

    #     max_pair = [copy.copy(inflection_point_indices[-4]), copy.copy(inflection_point_indices[-2])]
    if len(inflection_point_indices) < 2:
        max_pair = [0,0]
    # print "MAX_PAIR", max_pair
    # print inflection_point_indices
    return max_pair




def get_shadow(image, thresh=0.0, get_center=True, angle=0, flux_thresh = 0.0, ring_thresh=0.0):
    """ 
        get a single horizontal peak flux from 
        two sides of a centerpoint

        !!! IF YOU WANT get_center TO BE ANYTHING BUT TRUE
            YOU MUST SET IT EQUAL TO AN (X,Y) TUPLE!
        !!!
    """
    ''' sanitize input '''
    """ 
        get a single horizontal peak flux from 
        two sides of a centerpoint

        !!! IF YOU WANT get_center TO BE ANYTHING BUT TRUE
            YOU MUST SET IT EQUAL TO AN (X,Y) TUPLE!
        !!!
    """
    ''' sanitize input '''
    thresh = float(thresh)
    print_verbose("Threshold set to {0}".format(thresh))
    im = image
    im = im.rotate(angle)

    ''' get center of image if get_center is flagged '''
    if get_center ==  True:    
        (CENTER_X, CENTER_Y) = get_center_from_matrix(im.imvec, thresh)
        print_verbose("Got center as: x={0}, y={1}".format(CENTER_X, CENTER_Y))
    else:
        (CENTER_X, CENTER_Y) = get_center

    ''' get corresponding row and column from imvec 
        based on the center parsed above
    '''
    vec = im.imvec

    ''' if element is below threshold, set it to threshold '''
    # sub_threshold_indices = vec < (flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # sub_threshold_indices = vec > (.9-flux_thresh)*np.max(vec)
    # vec[sub_threshold_indices] = 0
    # # vec = vec[vec > flux_thresh*np.max(vec)]
 
    # reshape the image vector based on the squareroot of the length
    vec = vec.reshape((int(np.sqrt(vec.shape[0])), int(np.sqrt(vec.shape[0]))))
    print_verbose("Vec shape now: {0}".format(vec.shape))

    # extract the row and column using splicing
    center_row = vec[CENTER_X,:]
    center_col = vec[:,CENTER_Y]
    print_verbose("row")
    print_verbose(center_row)
    print_verbose("col")
    print_verbose(center_col)

    ''' get peaks of intensity distribution ''' 
    for i in range(0,98):
        try:
            row_peaks = argrelextrema(
                center_row, 
                np.greater, 
                order=100-i
            )
            if len(row_peaks[0]) != 2:
                continue
        except IndexError:
            continue
        break

    print "ARGSORT: ", np.min(np.absolute(center_row).argsort()[:10])

    print "ANGLE:", angle
    if angle <= math.pi/2.:
        def sub_thresh(a):
            return a-(center_row[row_peaks[0][-1]])
        center_row = np.asarray(map(sub_thresh, center_row))
        r = row_peaks[0][-1]
        args = np.absolute(center_row).argsort()[:15]
        args = args[np.where(args < np.max(row_peaks[0])) and args > np.min(row_peaks[0])]
        l = np.min(reject_outliers(args))
        print "L", l
    if angle > math.pi/2.:
        r = row_peaks[0][0]
        # print "R", r
        def sub_thresh(a):
            return a-(center_row[row_peaks[0][0]])
        center_row = np.asarray(map(sub_thresh, center_row))
        print center_row
        args = np.absolute(center_row).argsort()[:15]
        args = args[np.where(args < np.max(row_peaks[0])) and args > np.min(row_peaks[0])]
        print "ARGS:",args
        l = int(np.median(reject_outliers(args)))
        print "L", l



    # for xc in row_peaks[0]:
    #     plt.axvline(x=xc)
    plt.plot(center_row)
    plt.savefig("_WEIGHTED{0}.png".format(str(angle)))
    plt.clf()
    # plt.show()

    ''' get inflection points of intensity distribution '''
    i_spl = UnivariateSpline(range(len(center_row)),center_row,s=0,k=4)
    i_spl_2d = i_spl.derivative(n=0)
    new_i = np.asarray([i_spl_2d(x) for x in range(len(center_row))])
    # plt.plot(center_row)
    # plt.plot(new_i)
    # plt.show()
    print new_i
    ips = get_inflection_points(center_row, CENTER_X, image)


    # get the peaks from the array
    row_peaks = row_peaks[0][row_peaks[0] > 0]

    ''' convert coordinates using angle and return '''
    return convert_coordinates(l, r, CENTER_Y, angle, CENTER_X, CENTER_Y)

def find_nearest(array, value, r):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argsort()[:r]
    print "IDX", idx

def reject_outliers(data, m=1.5):
    return data[abs(data - np.mean(data)) < m * np.std(data)]


def FWHM(X,Y):
    half_max = max(Y) / 2.
    #find when function crosses line half_max (when sign of diff flips)
    #take the 'derivative' of signum(half_max - Y[])
    d = np.sign(half_max - np.array(Y[0:-1])) - np.sign(half_max - np.array(Y[1:]))
    #plot(X,d) #if you are interested
    #find the left and right most indexes
    left_idx = np.where(d > 0)[0][0]
    right_idx = np.where(d < 0)[-1][0]
    print left_idx
    print right_idx
    return X[right_idx] - X[left_idx] #return the difference (full width)

def find_fwhm(peak_big, peak_small, row):    
    # split the row down the middle
    division = int((peak_big + peak_small)/2.)
    left_half = row[:division]
    right_half = row[division:]
    
    # get left error
    lerror = FWHM(range(len(left_half)), left_half)
    print "lerror", lerror
    # get right error
    rerror = FWHM(range(len(right_half)), right_half)
    print "rerr", rerror

    return ((lerror+rerror)/(2.)) # https://en.wikipedia.org/wiki/Full_width_at_half_maximum
