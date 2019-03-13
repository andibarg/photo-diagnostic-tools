import os
import numpy as np
import PIL.Image
import PIL.ExifTags
from scipy import ndimage
import cv2

'''
Class for image
Specify path of jpg image.
Creates image array and
extracts EXIF data.
'''
class picture:
    def __init__(self,path):
        # Load image
        pic = PIL.Image.open(path)

        # Convert to array
        self.img = np.array(pic)

        # Extract Exif data
        try:
            self.exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in pic._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
        except:
            print('No EXIF data found.')

    '''
    RGB color histogram
    Outputs are arrays for the bins
    and histogram for each of the three colors.
    '''
    def rgb_hist(self):
        # Split color channels
        colchans = cv2.split(self.img)
        hists = []
        
        # Calculate histogram for each channel
        for ii, chan in enumerate(colchans):
            hists.append(cv2.calcHist([chan], [0], None, [256], [0, 256]))
        hists = np.squeeze(hists)

        # Get bins
        bins = np.arange(hists.shape[1])
        
        return bins, hists

    '''
    Focus peaking
    Parameters "radius", "amount", and "threshold"
    are for unsharp masking. May need to be adjusted
    depending on the image size.
    Outputs mask with the same size as the image.
    '''
    def focus_peak(self,radius=1,amount=500,threshold=6000):
        # Check if RGB or gray
        if len(self.img.shape)==3:
            im = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        else:
            im = self.img

        # Convert to float
        data = np.array(im, dtype=float)

        # High pass with gaussian filter
        lowpass = ndimage.gaussian_filter(data, 10)
        gauss_highpass = data - lowpass

        # Unsharp mask
        blurred = cv2.GaussianBlur(gauss_highpass, (4*radius+1, 4*radius+1), radius)
        unsharp = np.absolute((gauss_highpass-blurred)*amount)

        # Threshold mask
        peak = np.ones(blurred.shape)
        peak[unsharp < threshold] = np.nan

        return peak
    
    '''
    Highlight clipping warning
    Specify threshold for warning.
    Outputs mask with the same size as the image.
    '''
    def high_clip(self,threshold=250):
        # Check if RGB or gray
        if len(self.img.shape)==3:
            # Find maximum in each pixel
            im = np.max(self.img,axis=2)

        # Clipping mask
        clip = np.ones(im.shape)
        clip[im < threshold] = np.nan

        return clip

    '''
    Grid lines
    Choose file in the subfolder "grids"
    with coordinates of the grid lines.
    Ouputs x and y coordinates for the lines.
    '''
    def grid_lines(self,file='thirds.csv'):
        # Load grid file
        gpath = os.path.join(os.getcwd(),'grids',file)
        coords = np.loadtxt(gpath,delimiter=',')

        # Scale x, y for all lines
        x = coords[:,::2]*self.img.shape[1]
        y = coords[:,1::2]*self.img.shape[0]

        return x, y

'''
Example and plots
'''
if __name__ == "__main__":
    # Load example
    pic = picture('example.jpg')
    peak = pic.focus_peak()
    clip = pic.high_clip()
    bins, hists = pic.rgb_hist()
    xgrid, ygrid = pic.grid_lines('golden.csv')
    
    # Plot
    import matplotlib.pyplot as plt
    plt.style.use('fivethirtyeight')
    fig,ax = plt.subplots(2,2)
    
    ax[0,0].imshow(pic.img)
    ax[0,0].imshow(peak,cmap=plt.cm.bwr_r)
    ax[0,0].axis("off")
    ax[0,0].set_title("Focus peaking",fontsize=12)

    ax[0,1].imshow(pic.img)
    ax[0,1].imshow(clip,cmap=plt.cm.bwr)
    ax[0,1].axis("off")
    ax[0,1].set_title("Highlight clipping",fontsize=12)

    ax[1,0].imshow(pic.img)
    ax[1,0].plot(xgrid, ygrid,color=(0,1,0),linewidth=1)
    ax[1,0].axis("off")
    ax[1,0].set_title("Grid lines",fontsize=12)

    ax[1,1].bar(bins,hists[0],width=1.0,color=[1,0,0])
    ax[1,1].bar(bins,hists[1],width=1.0,color=(0,1,0))
    ax[1,1].bar(bins,hists[2],width=1.0,color=(0,0,1))       
    ax[1,1].bar(bins,np.minimum(hists[0],hists[1]),width=1.0,color=(1, 1, 0))
    ax[1,1].bar(bins,np.minimum(hists[1],hists[2]),width=1.0,color=(0, 1, 1))
    ax[1,1].bar(bins,np.minimum(hists[0],hists[2]),width=1.0,color=(1, 0, 1))
    ax[1,1].bar(bins,np.minimum.reduce(hists),width=1.0,color=(1, 1, 1))
    ax[1,1].axis("off")
    ax[1,1].set_ylim(0,255)
    ax[1,1].set_ylim(0,np.mean(np.minimum.reduce(hists))*4)
    ax[1,1].set_title("RGB histogram",fontsize=12)

    plt.savefig('example_diag.jpg', format='jpg', dpi=300)
    
    plt.show()
