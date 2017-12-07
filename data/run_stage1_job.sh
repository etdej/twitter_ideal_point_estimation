#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=5-00:00:00
#SBATCH --mem=7000
#SBATCH --job-name=smalll_1chain
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=slurm_%j.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/1013/jobs/stage1/run-${SLURM_JOB_ID/.*}
mkdir -p $RUNDIR
  
DATADIR=$SCRATCH/1013/data/stage1
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_SCRIPT=stage1.py
cp $PY_SCRIPT $RUNDIR 
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
python3 $PY_SCRIPT
echo "job finishing"
