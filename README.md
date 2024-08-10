# I2R Summer_Internship Code
A summary of all of Ryan Liu's code for his summer internship at I2R, A*Star. Worked under principal investigator Dr. Yu Yang. Ryan can be reached at ryanliu847@gmail.com for questions.

The work involved two types of heart images: LGE images and Cine images. The goal was to create an artificial intelligence segmentation method that would outperform a traditional U-Net in segmenting heart disease in both types of images.

The code has four sections:
  1. LGE baseline
  2. Cine baseline
  3. Two Stream
  4. 2D + 1D

The LGE and Cine baseline files were used to set a baseline for a rough accuracy for each image type. The LGE baseline was set at 74.7% dice coefficient while the Cine baseline was set at 62.4% dice coefficient. 

TWO STREAM AND 2D+1D SUMMARY HERE




The final presentation for the research can also be found below if additional information is required. 


NOTE: All code was run on google colab with paid compute units using a T4 with high RAM or L4 with high RAM. To accurately reproduce the results of this github, running the .pynb files on google colab with an L4 GPU is recommended.

While each section has a .py file along with a .ipynb file, the .py file might not function entirely properly with visualizations due to not being able to utilize the seperate cell function of google colab.  The .py file is simply an export of the .ipynb file into a .py file form and has not been created with non google colab use in mind.


