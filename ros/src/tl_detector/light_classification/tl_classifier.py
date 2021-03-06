from styx_msgs.msg import TrafficLight
import tensorflow as tf
import numpy as np
#import cv2

class TLClassifier(object):
    def __init__(self, is_site):
        #load classifier
        self.is_site = is_site
        self.colors = [TrafficLight.UNKNOWN, TrafficLight.GREEN, TrafficLight.RED, TrafficLight.YELLOW]
        self.colors_str = ['UNKNOWN', 'GREEN', 'RED', 'YELLOW']
        if is_site:
            graph_path = './light_classification/models/model_real/frozen_inference_graph.pb'
        else:
            graph_path = './light_classification/models/model_sim/frozen_inference_graph.pb'
        self.graph = tf.Graph()
        print(graph_path)
        with self.graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(graph_path, 'rb') as fid:
                od_graph_def.ParseFromString(fid.read())
                tf.import_graph_def(od_graph_def, name='')
            self.image_tensor = self.graph.get_tensor_by_name('image_tensor:0')
            self.boxes = self.graph.get_tensor_by_name('detection_boxes:0')
            self.scores = self.graph.get_tensor_by_name('detection_scores:0')
            self.classes = self.graph.get_tensor_by_name('detection_classes:0')
            self.num_detections = self.graph.get_tensor_by_name('num_detections:0')
        self.sess = tf.Session(graph=self.graph)
        #self.imcount = 0

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #implement light color prediction
        img_expand = np.expand_dims(image, axis=0)
        (boxes, scores, classes, num_detections) = \
            self.sess.run([self.boxes, self.scores, self.classes, self.num_detections], feed_dict={self.image_tensor:img_expand})
        boxes = np.squeeze(boxes)
        scores = np.squeeze(scores)
        classes = np.squeeze(classes).astype(np.int32)
        print('SCORES: ', scores[0])

        im_height, im_width, _ = image.shape
        if scores[0] < .9 and scores[0] > .35: #Deal with uncertainties in real images
            ymin, xmin, ymax, xmax = tuple(boxes[0].tolist())
            (left, right, top, bottom) = (int(round(xmin * im_width)), int(round(xmax * im_width)), 
                                          int(round(ymin * im_height)), int(round(ymax * im_height)))
            h = bottom - top + 1
            #cv2.imwrite('/home/workspace/sim_images/'+ str(self.imcount).zfill(4) +'.jpg', image)
            
            one_third = int(round(h/3))
            crop_img1 = image[top:top+one_third, left:right]
            crop_img2 = image[top+one_third:top+2*one_third, left:right]
            crop_img3 = image[top+2*one_third:top+h, left:right]
            light_array =  np.array([np.mean(crop_img3), np.mean(crop_img1), np.mean(crop_img2)])
            #print(str(self.imcount).zfill(4) + ' ' + self.colors_str[np.argmax(light_array) + 1])
            print(self.colors_str[np.argmax(light_array) + 1])
            return(self.colors[np.argmax(light_array) + 1])
        elif scores[0] >= 0.5:
            if classes[0] == 1:
                print('GREEN')
                return TrafficLight.GREEN
            elif classes[0] == 2:
                print('RED')
                return TrafficLight.RED
            elif classes[0] == 3:
                print('YELLOW')
                return TrafficLight.YELLOW
            else:
                print('UNKNOWN')
        else:
            print('UNKNOWN')
        #self.imcount += 1
        return TrafficLight.UNKNOWN

