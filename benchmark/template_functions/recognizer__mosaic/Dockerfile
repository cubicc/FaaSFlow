FROM codeless_base
RUN apt-get clean
RUN apt-get update
RUN apt-get install -y tesseract-ocr libgl1-mesa-glx
RUN pip3 install --no-cache-dir pillow opencv-python pytesseract

COPY config.py /proxy
RUN mkdir /blocks
COPY blocks /blocks
