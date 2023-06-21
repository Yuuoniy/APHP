## Installation
We provide two ways to install APHP: docker image and build from scratch.


### Docker
For easy usage, we provide a docker to use APHP, it works under ubuntu:20.04:

```shell
sudo docker build -t aphp:latest .
docker run -it --name "aphp-latest" "aphp:latest"

# if you have network problems that causes joern install to fail, add a proxy to your dockerfile.
ENV http_proxy=http://XX.XX.XX.XX:XXX
ENV https_proxy=http://XX.XX.XX.XX:XXX

# after you build, download the programs to test
cd /root
mkdir programs
git clone https://github.com/torvalds/linux.git
cd linux && git checkout v5.16-rc1
```


### From scratch 
You can build your environment by referring to the `Dockerfile` and the following steps for installing dependencies, APHP is based on several projects such as Joern, Gumtree and so on. 
   
```shell
ln -s /usr/bin/python3.9 /usr/bin/python

# install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py

# install python library
pip install -r requirements.txt 
```


For gumtree, we provide the gumtree (`tools/gumtree-3.1.0-install.zip`) built by us to make it easier, you can directly unzip and use the binary. This is built based on commit 7925aa5e0e7a221e56b5c83de5156034a8ff394f, with applying the `0001-ignore-tree-sitter-error-node.patch`. This patch is used to ignore tree-sitter errors, you can refer to this [issue](https://github.com/GumTreeDiff/gumtree/issues/276) to understand the patch.

```shell
# setup gumtree
unzip gumtree-3.1.0-install.zip
# the executebale is bin/gumtree

# install weggli
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh  (default)
cargo install weggli

# install joern
wget https://github.com/joernio/joern/releases/latest/download/joern-install.sh 
chmod +x ./joern-install.sh

./joern-install.sh --version=v1.1.763
```


```shell
# cd tools
# get tree-sitter-c
git clone https://github.com/tree-sitter/tree-sitter-c

# install standforenlp
wget https://nlp.stanford.edu/software/stanford-corenlp-4.4.0.zip
unzip stanford-corenlp-4.4.0.zip
```

Note that other versions of these tools may work, but we didn't test them.

### Config
If you install these tools by yourself, make sure configure the right paths so that APHP can find them.
Specifically, you may follow these steps:
```shell
ln -s ${YOUR_PATH}/APHP/tools/bin/gumtree /usr/bin/gumtree

# modify the TREE_SITTER_C_PATH in utils/config.py to the path of tree-sitter-c you cloned if not in 'tools'
# modify the TREE_SITTER_C_PATH in tools/tree-sitter-parser.py to the path of tree-sitter-c you cloned  if not in 'tools'

ln -s ${YOUR_PATH}/APHP/tools/tree-sitter-parser.py /usr/bin/tree-sitter-parser.py # for gumtree calls tree-sitter properly.
# modify the CORENLP_PATH in SpecificationExtraction/config.py to the path of stanford-corenlp-4.4.0 you unziped if not in 'tools'
```

### Download data
```shell
python -m spacy download en_core_web_sm
# download nltk data
python 
>> import nltk
>> nltk.download('punkt')
>> nltk.download('averaged_perceptron_tagger')
>> nltk.download('stopwords')
>> nltk.download('wordnet')
>> nltk.download('omw-1.4')
```

### Download programs to test
download the programs source code to test (as git repo). Modify `ULR` and `BRANCH` in `config/config.cfg` to the source code directory and the branch you want to test.
For example, you may download source code linux kernel in `/root/programs/`
```shell
git clone https://github.com/torvalds/linux.git
git checkout v5.16-rc1
```