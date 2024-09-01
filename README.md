# I2R Summer_Internship Code
A summary of all of Ryan Liu's code for his summer internship at I2R, A*Star. Worked under principal investigator Dr. Yu Yang. Ryan can be reached at ryanliu847@gmail.com for questions. 



**Project Objectives**

The work involved two types of heart images: LGE images and Cine images. The goal was to create an artificial intelligence segmentation method that would outperform a traditional U-Net in segmenting heart disease in both types of images.

The code has four sections:
  1. LGE baseline
  2. Cine baseline
  3. Two Stream
  4. 2D + 1D


**LGE and Cine Baseline Overview:**

The LGE and Cine baseline files were used to set a baseline for a rough accuracy for each image type. The LGE baseline achieved a 74.7% dice coefficient while the Cine baseline achieved a 62.4% dice coefficient. 


**Two Stream Overview**

Instead of the single encoder structure of the basic U-Net, the two stream approach uses two encoders, each with their own input. One encoder takes in a Cine input and the other takes in a LGE input. The final feature outputs of each of the encoders are concatenated channel wise, doubling the number of channels. However a standard decoder is used, so the concatenated output is compressed channel wise through use of a convolution block. Inputs for the U-Net skip connections come solely from the LGE encoder. 

**2D+1D Overview**

Instead of the LGE input of one frame of shape 3 x 224 x 224, the 2D + 1D model takes in a Cine file, with each Cine file containing 30 frames of shape 3 x 224 x 224. A singular encoder takes in the 30 frames one at a time. The end result after the encoder step is 30 different sets of feature outputs.

The 30 feature outputs are stacked to create a single tensor of shape 30 x 3 x 224 x 224, flattened to a 1 dimensional tensor, and then passed as an input to a 1D convolution block that compresses the temporal information from the 30 outputs into a single set of outputs. The output is then resized to shape 3 x 224 x 224 and passed to a standard decoder. 


**IMPORTANT NOTES FOR RUNNING MODEL**

  **1. Google Colab and GPU Resources**
    
  All code was run on google colab with paid compute units using a T4 with high RAM or L4 with high RAM. To accurately reproduce the results of this github, running the .pynb files on        google colab with an L4 GPU is recommended.

  While each section has a .py file along with a .ipynb file, the .py file might not function properly due to lacking the seperate cells of google colab and jupyter notebook.  The .py file is simply an export of the google colab file and has not been created with other IDE use in mind.

  **2. Indice Generation and Folder Organization**
  
  To run the model, it is recommended to copy the repository. For the data folder, please request a copy from Dr. Yu Yang and put it into the data folder. The data should be split into train_val, which contains training and validation images, and test, which contains testing images.

  The repository contains the following subfolders:
    Indices
      This folder will be used to store the pickle file with indices for the training and validation sets. The indices are generated in file "indice_generation". The models will load             the pickle file to set the indices for training and validation, so **run file indice_generation first**.
    Data
      train_val
        This will store the data for training and validation
      test
        This will store the data for testing
    Models
      This will store any model saves

  **3. Model Parameter Tunings**
    To tune model parameters including output_channels of the 1D layers in the 2D+1D model, the batch size, or number of frames, please look at the comments, where the lines will be marked with this comment in all caps: "PARAMETER TUNING: x parameter"
        




The final presentation for the research can also be found below. The final presentation contains a summary of certain hyperparameter tunings, overviews of the model approaches, and more. 

https://www.canva.com/design/DAGM_lxDlxk/7U6sktyukIvNfcVrU3EICA/edit?utm_content=DAGM_lxDlxk&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton

