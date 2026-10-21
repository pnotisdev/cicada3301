cd "$(dirname "$0")"
python run.py real 0 1
python run.py perm 0 200
python run.py fresh 0 200
python run.py plant_key 0 60 0.15
python run.py plant_key 100 40 0.25
python run.py plant_eng 0 40 1.0
echo done > alldone.txt
