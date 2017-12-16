#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=2
#SBATCH --time=6-20:00:00
#SBATCH --mem=10000
#SBATCH --job-name=fr_1chain
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=fr_%j.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/1013/jobs/stage1/fr/run-${SLURM_JOB_ID/.*}
mkdir -p $RUNDIR
  
DATADIR=$SCRATCH/1013/data/stage1/fr
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_UTILS=utils.py
PY_SCRIPT=stage1.py
cp $PY_SCRIPT $PY_UTILS $RUNDIR 
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
python3 $PY_SCRIPT
echo "job finishing"
