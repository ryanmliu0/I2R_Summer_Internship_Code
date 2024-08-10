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
The LGE and Cine baseline files were used to set a baseline for a rough accuracy for each image type. The LGE baseline was set at 74.7% dice coefficient while the Cine baseline was set at 62.4% dice coefficient. 


**Two Stream Overview**

**2D+1D Overview**




**IMPORTANT NOTES FOR RUNNING MODEL**

  **1. Google Colab and GPU Resources**
    All code was run on google colab with paid compute units using a T4 with high RAM or L4 with high RAM. To accurately reproduce the results of this github, running the .pynb files on        google colab with an L4 GPU is recommended.

    While each section has a .py file along with a .ipynb file, the .py file might not function entirely properly with visualizations due to not being able to utilize the seperate cell         function of google colab.  The .py file is simply an export of the .ipynb file into a .py file form and has not been created with non google colab use in mind.

  **2. Indice Generation and Folder Organization**
    To run the model, it is recommended to create a folder with all the available code, data, and other files needed.

    Within this main folder, it is recommended to create the following subfolders:
      Indices
        This folder will be used to store the pickle file with indices for the training and validation sets. The indices are generated in file "indice_generation". The models will load             the pickle file to set the indices for training and validation, so **run file indice_generation first**.
      Data
        train_val
          This will store the data for training and validation
        test
          This will store the data for testing
      Models
        This will store any model saves

      Any project code should just be stored in the main folder

  **3. Model Parameter Tunings**
    
        




The final presentation for the research can also be found below. The final presentation contains a summary of certain hyperparameter tunings, overviews of the model approaches, and more. 



