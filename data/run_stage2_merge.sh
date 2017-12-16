#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=10:00
#SBATCH --mem=5000
#SBATCH --job-name=usmergest2
#SBATCH --mail-type=ALL
#SBATCH --mail-user=dam740@nyu.edu
#SBATCH --output=slurm_%j.out

module purge
module load python3/intel/3.6.3

RUNDIR=$SCRATCH/1013/jobs/stage2/merge/us-run-${SLURM_JOB_ID/.*}
mkdir -p $RUNDIR
  
DATADIR=$RUNDIR
echo "Spawned job from node $(hostname) in directory $(pwd)"

PY_SCRIPT=merge_stage2.py
cp $PY_SCRIPT $RUNDIR
cd $RUNDIR

echo "running a job on node $(hostname) in directory $(pwd)"
python3 $PY_SCRIPT us
echo "job finishing"
