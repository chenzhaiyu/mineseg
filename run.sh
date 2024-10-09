
# clear

# python train.py class_weights=[1,1]
# cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_1_1/
# python predict.py result_dir='./outputs/unet/weights_1_1/'
# rm -r ./checkpoints/

# clear

# python train.py class_weights=[0.5,1]
# cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_05_1/
# python predict.py result_dir='./outputs/unet/weights_05_1/'
# rm -r ./checkpoints/

# clear

# python train.py class_weights=[0.25,1]
# cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_025_1/
# python predict.py result_dir='./outputs/unet/weights_025_1/'
# rm -r ./checkpoints/

# clear

# python train.py class_weights=[0.1,1]
# cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_01_1/
# python predict.py result_dir='./outputs/unet/weights_01_1/'
# rm -r ./checkpoints/

# clear


python train.py class_weights=[0.05,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_005_1/
python predict.py result_dir='./outputs/unet/weights_005_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.025,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_0025_1/
python predict.py result_dir='./outputs/unet/weights_0025_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.01,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_001_1/
python predict.py result_dir='./outputs/unet/weights_001_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.005,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_0005_1/
python predict.py result_dir='./outputs/unet/weights_0005_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.0025,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_00025_1/
python predict.py result_dir='./outputs/unet/weights_00025_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.001,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_0001_1/
python predict.py result_dir='./outputs/unet/weights_0001_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.0005,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_00005_1/
python predict.py result_dir='./outputs/unet/weights_00005_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.00025,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_000025_1/
python predict.py result_dir='./outputs/unet/weights_000025_1/'
rm -r ./checkpoints/

clear

python train.py class_weights=[0.0001,1]
cp ./checkpoints/unet/checkpoint_best.pth ./outputs/unet/weights_00001_1/
python predict.py result_dir='./outputs/unet/weights_00001_1/'
rm -r ./checkpoints/
