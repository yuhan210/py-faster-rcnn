#!/usr/bin/env python

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""

import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect, im_detect_batch
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse

CLASSES = ('__background__',
           'aeroplane', 'bicycle', 'bird', 'boat',
           'bottle', 'bus', 'car', 'cat', 'chair',
           'cow', 'diningtable', 'dog', 'horse',
           'motorbike', 'person', 'pottedplant',
           'sheep', 'sofa', 'train', 'tvmonitor')

NETS = {'vgg16': ('VGG16',
                  'VGG16_faster_rcnn_final.caffemodel'),
        'zf': ('ZF',
                  'ZF_faster_rcnn_final.caffemodel')}


def vis_detections(im, class_name, dets, thresh=0.5):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        return

    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')
    for i in inds:
        bbox = dets[i, :4]
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
            )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                  fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('test.jpg')
    plt.draw()

def batch_demo(net, img_names):
    """Detect object classes in an image using pre-computed object proposals."""

    # Load the demo image
    ims = []
    for image_name in img_names:
        #im_file = os.path.join(cfg.DATA_DIR, 'demo', image_name)
        im = cv2.imread(image_name)
        ims += [im] 
    # Detect all object classes and regress object bounds
    scores, boxes, batch_forward_time = im_detect_batch(net, ims)
    #scores, boxes = im_detect(net, im)
    #print ('Detection took {:.3f}s for '
    #       '{:d} object proposals').format(timer.total_time, boxes[0].shape[0])
    #print timer.total_time/float(len(img_names))
    # Visualize detections for each class
    '''
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for idx, im in enumerate(ims):
        for cls_ind, cls in enumerate(CLASSES[1:]):
            cls_ind += 1 # because we skipped background
            cls_boxes = boxes[idx][:, 4*cls_ind:4*(cls_ind + 1)]
            cls_scores = scores[idx][:, cls_ind]
            dets = np.hstack((cls_boxes,
                              cls_scores[:, np.newaxis])).astype(np.float32)
            keep = nms(dets, NMS_THRESH)
            dets = dets[keep, :]
            vis_detections(im, cls, dets, thresh=CONF_THRESH)
    '''
    return batch_forward_time

def demo(net, im):
    """Detect object classes in an image using pre-computed object proposals."""

    # Load the demo image
    #im_file = os.path.join(cfg.DATA_DIR, 'demo', image_name)
    #im = cv2.imread(im_file)

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(net, im)
    timer.toc()
    print ('Detection took {:.3f}s for '
           '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1 # because we skipped background
        cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        #vis_detections(im, cls, dets, thresh=CONF_THRESH)
    return timer.total_time

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        choices=NETS.keys(), default='zf')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    prototxt = os.path.join(cfg.MODELS_DIR, NETS[args.demo_net][0],
                            'faster_rcnn_alt_opt', 'faster_rcnn_test.pt')
    caffemodel = os.path.join(cfg.DATA_DIR, 'faster_rcnn_models',
                              NETS[args.demo_net][1])

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    #if args.cpu_mode:
    #    caffe.set_mode_cpu()
    #else:
    caffe.set_mode_gpu()
    caffe.set_device(args.gpu_id)
    cfg.GPU_ID = args.gpu_id

    print prototxt, caffemodel
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\n\nLoaded network {:s}'.format(caffemodel)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    img_folder = '/home/ubuntu/data/imagenet12/test'
    im_names = [] 
    for fid, f in enumerate(os.listdir(img_folder)):
        if fid == 512:
            break
        im_names += [os.path.join(img_folder, f)]

    #im_names = ['000456.jpg', '000542.jpg', '001150.jpg',
    #            '001763.jpg', '004545.jpg']
    batch_dict = {}  
    batch_sizes = [1, 2, 4]  
    for batch_size in batch_sizes:
        batches = []
        n_batch = len(im_names)/batch_size
        for i in xrange(n_batch):
            cur_batch = im_names[batch_size * i: batch_size * (i+1)] 
            batches += [cur_batch]
        batch_dict[batch_size] = batches 

    exec_time_dict = {}
    for batch_size in batch_sizes:
        exec_time = []
        for trail in xrange(10):
            total_batch_forward_time = 0
            for batch in batch_dict[batch_size]:
                #print len(batch)
                batch_forward_time = batch_demo(net, batch)
                total_batch_forward_time += batch_forward_time

            ave_img_exectime =  total_batch_forward_time / float(len(im_names))
            print 'batch_size:', batch_size, ' exectime/batch:', total_batch_forward_time/float(len(batch_dict[batch_size])), 'exectime/img:', ave_img_exectime
            exec_time += [ave_img_exectime]
        exec_time_dict[batch_size] = exec_time 

    for batch_size in batch_sizes:
        print np.mean(exec_time_dict[batch_size]), np.std(exec_time_dict[batch_size])
    '''
    video_path = '/home/ubuntu/videos/14_year_old_girl_playing_guitar_cover_van_halen__eruption_solo_hd_best_quality_fDTm1IzQf-U.mp4'
    cap = cv2.VideoCapture(video_path)
    fid = 0
    exec_time = []
    while(cap.isOpened()):
        ret, frame = cap.read()
        t = demo(net, im)
        print fid
        fid += 1
        exec_time += [t]
    import pickle
    with open('times.pickle', 'wb') as fh:
        pickle.dump(exec_time, fh)
    #plt.show()
    '''
