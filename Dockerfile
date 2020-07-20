FROM python:3.6
WORKDIR /code
COPY requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
EXPOSE 19542 8080
COPY . .
CMD sh pro.sh
