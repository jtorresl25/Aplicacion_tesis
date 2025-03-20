streamlit run app.py

install torch 

pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124



gcloud builds submit --tag gcr.io/lupz-365519/test-app  --project=lupz-365519

gcloud run deploy --image gcr.io/lupz-365519/test-app --platform managed  --project=lupz-365519 --allow-unauthenticated --concurrency 80 --region us-central1

gcloud run services update test-app --session-affinity

test-app
33 regions

https://www.youtube.com/watch?v=LxwoCKM1Qik

gcloud app deploy app.yaml --project=lupz-36551
https://www.youtube.com/watch?v=o4sxWlSxpXk&ab_channel=SistemasInteligentes