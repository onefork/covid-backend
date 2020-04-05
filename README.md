# covid-backend

Install via

```bash
pip install -r requirements.txt
```

Run

```bash
python papers.py
```

Test

```bash
http --session-read-only=./session localhost:8000/papers q=="whats corona"
```


# download data for browser:

download the folder *models* from 
https://drive.google.com/open?id=1cpPeaxlvNZ6p-2XyDk4p8IzeAVCt0k1p
and place it inside the main folder.

the structure will be covid-backend > models > scibert-nli > etc.

download the data from kaggle :
https://www.kaggle.com/allen-institute-for-ai/CORD-19-research-challenge
Place this as the data folder (in the main folder) and add the file 
*metadata_codevscovid.csv* to the data folder: 
https://drive.google.com/open?id=13FaD9-ugzBgysNnNwIhzgbl51sCrxxSi

the structure will be covid-backend > data > (all the data from kagle (i.e biorxiv_medrxiv folder, comm_use_subset folder,  metadata.readme file etc.) + metadata_codevscovid.csv)
