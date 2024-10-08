# -*- coding: utf-8 -*-
"""1.1 LGE Baseline.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_us2sc4fYVX-oSazJIDA3Tm9ye2vAXl7

# Imports and Setting Seed
"""

#For the use of google colab. Connects to google drive, which acts as storage for loading files, data, and models. Comment this out if not using google colab.
from google.colab import drive
drive.mount('/content/drive')

#Also for use of google colab. Imports packages that google colab does not have preinstalled.
!pip3 install segmentation_models_pytorch
!pip3 install warmup_scheduler

#Import packages

import torch.utils.data as Data
import torch
import segmentation_models_pytorch as smp
import segmentation_models_pytorch.losses as smp_losses
import segmentation_models_pytorch.utils as smp_utils
from torchsummary import summary
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
import cv2
import datetime
import random
import sys
from torch.optim.lr_scheduler import StepLR
from warmup_scheduler import GradualWarmupScheduler
from copy import deepcopy
import torchvision.utils as vutils
import ssl

#Define GPU use
torch.set_num_threads(6)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#Define set seed

seed_cus = 1

random.seed(seed_cus)
np.random.seed(seed_cus)
torch.manual_seed(seed_cus)
torch.cuda.manual_seed(seed_cus)
torch.cuda.manual_seed_all(seed_cus)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'

def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

g = torch.Generator()
g.manual_seed(seed_cus)

"""# Load Data"""

#Define dataset class

import torch.utils.data as Data
class My_Datasets(Data.Dataset):
    def __init__(self, img_dir, mask_dir, transform1=None,transform2=None):
        super().__init__()

        #Set paths to the LGE directory and mask directory
        self.img_dir = img_dir
        self.mask_dir = mask_dir


        #Get a list of all the files in the LGE and mask directories
        self.img_list = os.listdir(self.img_dir)
        self.mask_list = os.listdir(self.mask_dir)

        #Initialize transforms
        self.transform1 = transform1
        self.transform2 = transform2

    def __getitem__(self, index):

        #Define the LGE file name
        img_name = self.img_list[index]

        #Define the mask file name using the LGE file name so the masks and the LGE images match up
        mask_name = self.img_list[index].split('.')[0] + "_0000.nii.png"



        if img_name.endswith('.png'):

            #Load LGE images and masks
            img = cv2.imread(os.path.join(self.img_dir,img_name))
            mask= cv2.imread(os.path.join(self.mask_dir,mask_name))

            #Make sure LGE images and masks are not corrupted and have type None
            if type(img) != type(None) or type(mask) != type(None):


              #Normalize - masks are already labeled 1-3, so no need to divide by 255
              LABImg = img/[255.0]
              LABmask = mask/[1.0]

              #Resize
              LABImg = cv2.resize(LABImg,(224,224))
              LABmask = cv2.resize(LABmask,(224,224))

              #Convert to float
              LABImg = LABImg.astype(np.float32)
              LABmask = LABmask.astype(np.float32)
              LABmask = LABmask[:,:,0]


              #Apply transforms on the images and the masks
              if self.transform1:
                LABImg = self.transform1(LABImg)
                LABmask = self.transform2(LABmask)


              return LABImg, LABmask, img_name
            else:
              print(img_name)

    def __len__(self):
        return len(self.img_list)


#Define transforms

transforms_img = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.485, 0.456, 0.406),(0.229, 0.224, 0.225))
])
transforms_mask = transforms.Compose([
    transforms.ToTensor(),
])

# Define batch size, image paths, and create an object of the dataset class made above


img_path = '/content/drive/My Drive/Internship_24_Ryan/Heart/Data/train_val/LGE/'
mask_path = '/content/drive/My Drive/Internship_24_Ryan/Heart/Data/train_val/masks/'


batch_size_train = 8
batch_size_val = 8

train_set = My_Datasets(img_path,mask_path, transform1=transforms_img,transform2=transforms_mask)
n_train = len(train_set)
split = n_train // 5
a = list(range(n_train))

#Prepare a visualization to double check the LGE images and masks are paired correctly - also serves as a visualization for presentations

#Made for use with google colab cells - if not using google colab might want to change this
plt.imshow(train_set[8][0].permute(1,2,0))
plt.imshow(train_set[8][1].permute(1,2,0), alpha = 0.5, cmap = "jet")

#Load pickle files with indices meant for training vs testing

#NOT APPLICABLE IF THIS IS THE FIRST TIME RUNNING THE CODE
#BELOW CODE WILL CREATE THESE PICKLE FILES

with open('/content/drive/My Drive/Internship_24_Ryan/Heart/Indices/train_indices.pkl', 'rb') as f:
  train_indices = pickle.load(f)

with open('/content/drive/My Drive/Internship_24_Ryan/Heart/Indices/val_indices.pkl', 'rb') as f:
  val_indices = pickle.load(f)

#Create training/validation splits and define the indices that are meant for training vs validation
#Save indices to pickle file(use above code if already generated pickle files)

names = os.listdir(img_path)

#Group patient files together so that all of a patient's files are in one group
#This is to later ensure that all patient files are only in either training, validation, or testing.
#This prevents the model from cheating by looking at similar images in both training and validation/testing
grouped_names = {}

for i in range(len(names)):
  base = names[i].split('_')[0]

  if names[i] not in blacklisted:
    if len(grouped_names) == 0:
      grouped_names[base] = [names[i]]
    else:
      if base in grouped_names:
        grouped_names[base] += [names[i]]
      else:
        grouped_names[base] = [names[i]]

indices = list(range(n_train))

#Attach an index to each file
for i in range(len(train_set)):
  tri = train_set[i]
  base = tri[2].split('_')[0]
  for x in range(len(grouped_names[base])):
    name = grouped_names[base][x]
    if name == tri[2]:
      grouped_names[base][x] = [name, i]

#Get indices for training, validation, and testing.
length = len(train_set)
val_len = length // 4

train_indices = []
val_indices = []

train_names = []
val_names = []

train_len = length - val_len
for patient in grouped_names:
  while len(train_indices) < train_len:
    for index in range(len(grouped_names[patient])):

      train_indices += [grouped_names[patient][index][1]]
      train_names += [grouped_names[patient][index][0]]

    break

  else:
    while len(val_indices) < val_len:
      for index in range(len(grouped_names[patient])):
        val_indices += [grouped_names[patient][index][1]]
        val_names += [grouped_names[patient][index][0]]
      break

#check to make sure no indices are repeated
for name in train_indices:
  if name in val_indices:
    print("DUPLICATE EXISTS!")
    print(name)

#check to make sure no patients have images in both the training and testing
train_bases = set()
val_bases = set()

for name in train_names:
  base = name.split('_')[0]
  train_bases.add(base)
for name in val_names:
  base = name.split('_')[0]
  val_bases.add(base)

for base in train_bases:
  if base in val_bases:
    print("ERROR")
    print(base)

#Check to make sure the length of each are valid
print(len(train_indices))
print(len(val_indices))

# define fixed seed
random.seed(seed_cus)
# define fixed seed
torch.manual_seed(seed_cus)
torch.cuda.manual_seed(seed_cus)
torch.cuda.manual_seed_all(seed_cus)
indices = random.sample(a, len(a))

#Given a list of indices meant for training, create a Dataloader that will create a training set and batches
#Do the same for validation as well


train_sampler = torch.utils.data.sampler.SubsetRandomSampler(train_indices)

# define fixed seed
torch.manual_seed(seed_cus)
torch.cuda.manual_seed(seed_cus)
torch.cuda.manual_seed_all(seed_cus)

valid_sampler = torch.utils.data.sampler.SubsetRandomSampler(val_indices)

train_loader = Data.DataLoader(
    dataset=train_set,
    sampler=train_sampler,
    num_workers=0,
    batch_size=batch_size_train,
    pin_memory=True,
    worker_init_fn=seed_worker,
    generator=g)
valid_loader = Data.DataLoader(
    dataset=train_set,
    sampler=valid_sampler,
    num_workers=0,
    batch_size=batch_size_val,
    pin_memory=True,
    worker_init_fn=seed_worker,
    generator=g)

"""# Loading Pretrained Senet154 Weights"""

#Allow Senet154 to be loaded
ssl._create_default_https_context = ssl._create_unverified_context

# Load an SeNet154 through the smp.Unet library

#CHANGE BACKBONE HERE!!!

#Replace 'senet154' with 'resnet50' or different backbones. See full list of available backbones in the segmentation_models_pytorch library. NOTE: Resnet50 is much faster to load than an senet154.
model_phx = smp.Unet('senet154',encoder_weights='imagenet', in_channels=3, classes=4)

#Send model to GPU
model_phx= nn.DataParallel(model_phx)
model_phx.to(device)

"""# Define Training"""

# Commented out IPython magic to ensure Python compatibility.
#Define training
def train(epoch, alpha, beta):
    loss_sum = 0
    prev_time = time.time()
    for i, (images, masks, names) in enumerate(train_loader):

        #Send both imgs and masks to GPU
        imgs = images.to(device=device,dtype=torch.float32)
        masks = masks.to(device=device,dtype=torch.float32)

        #Turn masks from type Torch.Tensor to Torch.LongTensor
        #Why? Not sure, but it throws an error if masks aren't type LongTensor
        masks = masks.long()

        #Use model to predict on the images
        masks_pred = model_phx(imgs)


        #Calculate loss
        loss_seg = alpha * criterion_FA(masks_pred, masks)
        loss_all = loss_seg
        iter_loss = loss_all.data.item()
        loss_sum += loss_all.item()


        #Calculate gradients and begin backwards propagation
        optimizer.zero_grad()
        loss_all.backward()
        optimizer.step()


        #Print output of each batch and epoch
        batches_done = epoch * len(train_loader) + i
        batches_left = num_epoch * len(train_loader) - batches_done
        time_left = datetime.timedelta(seconds=batches_left * (time.time() - prev_time))
        prev_time = time.time()

        sys.stdout.write(
            "\r[Epoch %d/%d] [Batch %d/%d] [loss_seg: %f] [loss: %f]  ETA: %s"
#             % (
                epoch,
                num_epoch,
                i,
                len(train_loader),
                loss_seg.item(),
                loss_all.item(),
                time_left,
            )
        )


# Define validation
def val(epoch, alpha, beta):
    #Define variables
    loss_sum = 0
    global best_seg_loss
    running_loss_all = 0.0
    running_loss_seg = 0.0
    prev_time = time.time()

    for i, (images, masks, names) in enumerate(valid_loader):
        #Send images and masks to GPU
        imgs = images.to(device=device,dtype=torch.float32)
        masks = masks.to(device=device,dtype=torch.float32)
        batch_size = imgs.shape[0]


        #Turn masks into type LongTensor, see explanation in train function
        masks = masks.long()

        with torch.no_grad():
            #Set to eval so weights don't change
            model_phx.eval()


            #Predict
            masks_pred = model_phx(imgs)

            #Calculate loss
            loss_seg = alpha * criterion_FA(masks_pred, masks)
            loss_all = loss_seg
            iter_loss = loss_all.data.item()
            loss_sum += loss_all.item()
            running_loss_seg += loss_seg.item() * batch_size
            running_loss_all += loss_all.item() * batch_size

            #Print output loss for the validation stage of an epoch
            batches_done = epoch * len(valid_loader) + i
            batches_left = num_epoch * len(valid_loader) - batches_done
            time_left = datetime.timedelta(seconds=batches_left * (time.time() - prev_time))
            prev_time = time.time()

            sys.stdout.write(
            "\r[Epoch %d/%d] [Batch %d/%d] [loss_seg: %f] [loss: %f]  ETA: %s"
#             % (
                epoch,
                num_epoch,
                i,
                len(valid_loader),
                loss_seg.item(),
                loss_all.item(),
                time_left,
            )
        )


    # len of valid_loader here is the total number of image, thus divided by 10
    epoch_loss_seg = running_loss_seg / (len(valid_loader.dataset)/5)
    epoch_loss_all = running_loss_all / (len(valid_loader.dataset)/5)

    # skip one line
    keyword = os.linesep
    print(keyword)

    sys.stdout.write(
        "[Epoch %d/%d] [loss_seg: %f] [loss: %f]"
#         % (
            epoch,
            num_epoch,
            epoch_loss_seg,
            epoch_loss_all,
        )
    )

    #If the model loss is the best so far, save it
    epoch_loss_seg_adj = epoch_loss_seg/alpha
    if epoch_loss_seg_adj < best_seg_loss:
        best_seg_loss = epoch_loss_seg_adj
        torch.save(model_phx.state_dict(), '/content/drive/My Drive/Internship_24_Ryan/Heart/Models/LGE_baseline.pt')

# Define training parameters here
# Experiment with different losses, optimizers, learning rate, epochs
# Adam and dice loss in general were found to be the best

num_epoch = 50
learning_rate = 1e-4

criterion_FA = smp_losses.dice.DiceLoss(smp_losses.MULTICLASS_MODE, from_logits=True) # new loss (multi) in losses
optimizer = optim.Adam(model_phx.parameters(),
                           lr=learning_rate)

scheduler_cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, 50)
scheduler_warmup = GradualWarmupScheduler(optimizer, multiplier=2, total_epoch=5, after_scheduler=scheduler_cosine)
device = torch.device('cuda')

"""# Training"""

#Training


#Send loss to GPU
criterion_FA = criterion_FA.cuda()

alpha = 1.0
beta = 0.0


best_seg_loss = 999999
for epoch in range(num_epoch):
    print('Starting training epoch {}/{}.'.format(epoch + 1, num_epoch))
    model_phx.train()
    train(epoch, alpha, beta)
    scheduler_warmup.step()
    print(scheduler_warmup.get_lr())
    print('Starting validation epoch {}/{}.'.format(epoch + 1, num_epoch))
    model_phx.eval()
    val(epoch, alpha, beta)
    print(scheduler_warmup.get_lr())
    print('Best adjusted seg loss for validation dataset: {}.'.format(best_seg_loss))

"""# Evaluation"""

#Retrieve some test data
img, mask, names = next(iter(train_loader))

#Load model from previous saved model or from other model
model_phx.load_state_dict(torch.load('/content/drive/My Drive/Internship_24_Ryan/Heart/Models/LGE_baseline.pt'))
#Send model to GPU
model_test = model_phx.cuda()


#Predict on images for visualization
with torch.no_grad():
    model_test.eval()
    mask_pre = model_test(img.cuda())

#Visualizations of the image, mask, and prediction

#Show image
# plt.figure(figsize=(64,64))
# plt.axis("off")
# plt.title("Testing Images")
# plt.imshow(np.transpose(vutils.make_grid(img[0:], padding=2, normalize=True).cpu(),(1,2,0)))
# fig = plt.imshow(np.transpose(vutils.make_grid(img[0:], padding=2, normalize=True).cpu(),(1,2,0)))
# ##fig.figure.savefig("/content/drive/My Drive/Internship_24_Ryan/Script/Brain MRI/exp_2_ground_label_seg/results/Fully S-multiclass-smploss-s1/Testing Images V1.png", dpi=224)


#Show mask
plt.figure(figsize=(64,64))
plt.axis("off")
plt.title("Annotation masks")
plt.imshow(np.transpose(vutils.make_grid(mask[0:], padding=2, normalize=True).cpu(),(1,2,0)))
fig = plt.imshow(np.transpose(vutils.make_grid(mask[0:], padding=2, normalize=True).cpu(),(1,2,0)))
#fig.figure.savefig("/content/drive/My Drive/Internship_24_Ryan/Script/Brain MRI/exp_2_ground_label_seg/results/Fully S-multiclass-smploss-s1/Annotation masks V1.png", dpi=224)


#Show prediction
# here we have to use mask_pre[0:,1].unsqueeze(1) - select 2nd channel as mask output and add one more dimension for 16,1,224,224 for image display
plt.figure(figsize=(64,64))
plt.axis("off")
plt.title("Predicted results")
plt.imshow(np.transpose(vutils.make_grid(mask_pre[0:,1].unsqueeze(1), padding=2, normalize=True).cpu(),(1,2,0)))
fig = plt.imshow(np.transpose(vutils.make_grid(mask_pre[0:,1].unsqueeze(1), padding=2, normalize=True).cpu(),(1,2,0)))
#fig.figure.savefig("/content/drive/My Drive/Internship_24_Ryan/Script/Brain MRI/exp_2_ground_label_seg/results/Fully S-multiclass-smploss-s1/Predicted results V1.png", dpi=224)

#In use for colab, downgrade pandas here for later evaluation code
!pip3 install pandas==1.5.3

#IMport libraries
import os
import numpy as np
import pandas as pd

# specify the folder path for testing dataset
directory = '/content/drive/My Drive/Internship_24_Ryan/Heart/Data/test/LGE'

# number of file in directory
dirListing = os.listdir(directory)
row_num = len(dirListing)

# load empty excel file for recording filename
df = pd.read_csv(
    "/content/drive/My Drive/Internship_24_Ryan/Heart/Temp/Filename.csv")




#Most of the below code from 'for i in range(row_num)' to 'df_final.to_csv' is outdated and reduntant - don't believe its actually useful later"

# add blank row to df for saving ID

for i in range(row_num):
    df = df.append({'ID': i}, ignore_index=True)
df_temp = df

# write ID to final excel file
df_final = df_temp
counter = 0
for filename in os.listdir(directory):
    if filename.endswith(".tiff"):
        df_final['ID'][counter] = filename
        counter += 1

        continue
    else:
        continue

df_final.to_csv(
    '/content/drive/My Drive/Internship_24_Ryan/Heart/Temp/Filename filled.csv',
    index=False)

from types import NoneType

# total number of testing dataset
length = df['ID'].size

# other customized DICE calculation fuction - not in use
def single_dice_coef(y_true, y_pred_bin):
    # shape of y_true and y_pred_bin: (height, width)
    intersection = np.sum(y_true * y_pred_bin)
    if (np.sum(y_true) == 0) and (np.sum(y_pred_bin) == 0):
        return 1
    return (2 * intersection) / (np.sum(y_true) + np.sum(y_pred_bin))

# other customized DICE calculation fuction - not in use
def mean_dice_coef(y_true, y_pred_bin):
    # shape of y_true and y_pred_bin: (height, width, n_channels)
    channel_num = y_true.shape[-1]
    mean_dice_channel = 0.
    for j in range(channel_num):
        channel_dice = single_dice_coef(y_true[:, :, j], y_pred_bin[:, :, j])
        mean_dice_channel += channel_dice / (channel_num)
    return mean_dice_channel

# standard DICE calculation fuction
def dice_coef2(y_true, y_pred):
    y_true_f = y_true.flatten()
    y_pred_f = y_pred.flatten()
    union = np.sum(y_true_f) + np.sum(y_pred_f)
    if union == 0:
        return 1
    intersection = np.sum(y_true_f * y_pred_f)
    score = 2. * intersection / union
    #print(score)
    return 2. * intersection / union

#Import libraries
from scipy.stats import logistic
import gc

#Define variables for average dice coefficient score
score_1 = 0
count = 0
i = 0
lst = []

#Define the total amount of accuracy for each of the labels and the count of each label for individual label accuracy
label_1 = 0
label_2 = 0
label_3 = 0
count_1 = 0
count_2 = 0
count_3 = 0



#Define paths for the test images
img_path_test = '/content/drive/My Drive/Internship_24_Ryan/Heart/Data/test/LGE/'
mask_path_test = '/content/drive/My Drive/Internship_24_Ryan/Heart/Data/test/masks/'


#Define testing dataset
test_set_phx = My_Datasets(img_path_test, mask_path_test, transform1=transforms_img, transform2=transforms_mask)
n_test = len(test_set_phx)
test_loader_phx = Data.DataLoader(dataset=test_set_phx,num_workers=0,batch_size=1,pin_memory=True)

#Calculate avg dice score and individual label dice score
for i, (image, mask, filename) in enumerate(test_loader_phx):

    #Send images and masks to GPU
    img = image.to(device=device,dtype=torch.float32)
    mask = mask.to(device=device,dtype=torch.float32)


    #Predict on images and apply softmax function for multiclass segmentation
    with torch.no_grad():
        model_test.eval()
        pre = model_test(img.cuda())
        pred = torch.softmax(pre, dim = 1)



    if type(pred) != type(None) and type(mask) != type(None):
      img_score = 0



      #Go through each label
      for layer in range(3):

        #The model returns an output of shape (4,224,224), with each of the channels being one label's prediction. For example, pred[2] defines the area that the model thinks belongs to Label 2
        #However, the mask is shape (1,224,224), with the different labels simply having different values, with the area of Label 2 being all the pixels that have value 2
        #Label 0 is the background label, the non-disease label, so we do not use it in our evaluation of the dice score

        #Get the ground truth area of the label the for loop is currently on
        temp_mask = np.where(mask.cpu().numpy() == layer+1, 1, 0)

        #Get the predicted area of the label the loop is on
        temp_pred = np.where(pred[0][layer+1].cpu().numpy() > 0.5, 1, 0)


        #Calculate the dice score
        score_temp = dice_coef2(temp_mask, temp_pred)

        #Add the dice score to the sum of all accuracies
        img_score += score_temp



        #If the label is 1, add it to the dice score sum for layer 1 and add one to the number of files that have label 1
        #Continue for all labels

        #Remember that if layer == 0, that means the Label is 1
        #Label 0 is the background layer, and Label 1-3 are heart disease labels
        if layer == 0:
          label_1 += score_temp
          count_1 += 1
        elif layer == 1:
          label_2 += score_temp
          count_2 += 1
        elif layer == 2:
          label_3 += score_temp
          count_3 += 1

      #Divide the image score by 3 for each of the labels
      final_img_score = img_score/3

      #Add it to a list
      lst += [[final_img_score, df['ID'][i]]]

      #Add final_img_score to score_1, which is the current avg dice coefficient across all images
      score_1 = score_1 + final_img_score
      count += 1
    else:
      print(i)


#Print results

print("Dice Coefficient", score_1/count)
print("Label 1 score: ", label_1/count_1)
print("Label 2 score: ", label_2/count_2)
print("Label 3 score: ", label_3/count_3)

