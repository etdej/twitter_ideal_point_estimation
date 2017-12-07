#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=20
#SBATCH --time=30:00
#SBATCH --mem=60000
#SBATCH --job-name=stage2
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=stage2_%A_%a.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/1013/jobs/stage2/array-${SLURM_ARRAY_JOB_ID}/run-${SLURM_ARRAY_TASK_ID}
mkdir -p $RUNDIR
  
DATADIR=$SCRATCH/1013/data/stage2
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_SCRIPT=stage2.py
cp $PY_SCRIPT $RUNDIR
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
first=$((1800 * $SLURM_ARRAY_TASK_ID))
last=$(($first + 1800))
N_ITER=2000
N_WARMUP=1000
python3 $PY_SCRIPT $N_ITER $N_WARMUP $first $last
echo "job finishing"
