# coding:utf8
from qiniu import Auth, put_file, etag, urlsafe_base64_encode, put_data
import qiniu.config

access_key = 'nrL2RMP5dkv0Z4hHtWyo5-RBBDGyfRrcHqqWppi2'
secret_key = 'Ztz8olT8r_952F0e55jxA381rwUTg6uHPxn_j02n'


def storage(file_data):
    # 构建七牛云存储对象
    q = Auth(access_key, secret_key)
    # 存储的空间
    bucket_name = 'ihome'
    # 生成上出啊你的空间， 可以设置过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 上传动作
    ret, info = put_data(token, None, file_data)
    print type(info)
    print ret
    if info.status_code == 200:
        return ret.get("key")
    else:
        raise Exception("上传失败")


if __name__ == '__main__':
    with open("/home/python/Desktop/fruit.jpg", "rb") as f:
        file_data = f.read()
        print file_data
    storage(file_data)
