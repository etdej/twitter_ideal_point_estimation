#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=20
#SBATCH --time=04:00:00
#SBATCH --mem=70000
#SBATCH --job-name=fr_stage2
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=stage2_%A_%a.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/1013/jobs/stage2/france/array-${SLURM_ARRAY_JOB_ID}/run-${SLURM_ARRAY_TASK_ID}
mkdir -p $RUNDIR
  
DATADIR=$SCRATCH/1013/data/stage2/france
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_SCRIPT=stage2_fr.py
cp $PY_SCRIPT $RUNDIR
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
first=$((1415 * $SLURM_ARRAY_TASK_ID))
last=$(($first + 1415))
N_ITER=2000
N_WARMUP=1000
python3 $PY_SCRIPT $N_ITER $N_WARMUP $first $last
echo "job finishing"
