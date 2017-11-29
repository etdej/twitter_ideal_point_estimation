#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=1:00:00
#SBATCH --mem=100000
#SBATCH --job-name=twochains
#SBATCH --mail-type=END
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=slurm_%j.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/dam740/run-${SLURM_JOB_ID/.*}
mkdir -p $RUNDIR
  
DATADIR=$SCRATCH/1013/data
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_SCRIPT=stage1.py
cp $PY_SCRIPT $RUNDIR 
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
echo "Running job!"
echo "Data dir: $DATADIR"
echo "Calling python..."
python3 $PY_SCRIPT
echo "Out of python"
echo "finishing"
