The dataset is sitting on [Registry of Open Data on AWS (RODA)](https://registry.opendata.aws/openfold/). 

To install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html):
```shell
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli
```

To measure the size without downloading:
```ssh
nohup aws s3 ls --no-sign-request s3://openfold/ --recursive --human-readable --summarize > openfold_list.txt 2>&1
```
Total size is 4.9Tb.

To download: 
```
nohup ~/tools/aws/aws/dist/aws s3 sync --no-sign-request s3://openfold ./roda_raw/ >aws_s3.out 2>aws_s3.err &
```
Takes 2 days and 4 hours. The dataset takes 5.1Tb on disk, according to `du -sh`.

