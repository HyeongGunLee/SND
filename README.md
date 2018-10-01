
# Speech Notification Device for Blind

## Description
_Speech Notification Device_ using tensorflow, RaspberryPi, and TTS
Thanks to advance of machine learning and easy to use of libraries, we can help people 
who have a difficulty in their life. In this project, we explain about a device which can help
blind using image recognition, text detection technology. The device are implemented using RaspberryPi,
camera, and some detection sensors.

## Implementation
### Image Recognition
[inception-v3](https://www.tensorflow.org/tutorials/images/image_recognition) trained with [ImageNet](http://image-net.org/) data was used to implement image recognition feature.
## Text Detection
[Google Cloud Platform Vision API](https://cloud.google.com/vision/) supports **Optical Character Recognition** API and this api was used to implement text detection feature.
_Example_
```json
 {
  "requests": [
    {
      "image": {
        "content": "sample content"
      },
      "features": [
        {
          "type": "TEXT_DETECTION"
        }
      ]
    }
  ]
 }
```

## Server/Client
* Client 
  - using `socket` library, send an encoded image data to server
  
* Server
  - receive data from client using socket and decode image data
  - perform image recognition and text detection function
  - send a response to the client

