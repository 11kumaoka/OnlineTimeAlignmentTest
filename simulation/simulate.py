"""Independent stage; invoke with python3 -m simulation.simulate."""
import json
from pathlib import Path
from research_common import REPO, cli_parser, run, require, stage, done, digest, execute, write_json

def check_simulation(out,events):
    import uproot
    with uproot.open(out) as f:
        tree=f['events']
        for name in ('SiMAPSHits','MPGDHits','ACLGADHits'):
            if name not in tree:raise RuntimeError(f'Missing simulation collection {name}')
        if tree.num_entries<events:raise RuntimeError('Simulation has fewer events than requested')
        return tree.num_entries

def simulate(a):
    require(a.run_dir,'step1')
    cfg=json.loads(a.config.read_text())
    if cfg['events'] <= 0: raise ValueError('events must be positive')
    p=stage(a.run_dir,'step2')
    write_json(p/'config.json',cfg)
    out=p/'events.edm4hep.root'
    if a.sim_input:
        if not a.sim_input.is_file():raise FileNotFoundError(a.sim_input)
        out.symlink_to(a.sim_input.resolve())
        done(p,source=str(a.sim_input.resolve()),sha256=digest(out),input_events=check_simulation(out,cfg['events']),mode='existing simulation; no Geant4 run')
        return
    b=cfg['beam']
    cmd=['ddsim','--compactFile',a.run_dir/'step1/misaligned.xml','--outputFile',out,
         '--numberOfEvents',str(cfg['events']),'--enableGun','--gun.particle',b['particle'],
         '--gun.energy',f"{b['energy_GeV']}*GeV",'--gun.thetaMin',str(b['theta_min']),
         '--gun.thetaMax',str(b['theta_max']),'--gun.phiMin',str(b['phi_min']),
         '--gun.phiMax',str(b['phi_max']),'--gun.distribution','uniform',
         '--gun.position='+' '.join(f'{v}*mm' for v in b.get('position_mm',[0.0,0.0,0.0])),
         '--vertexSigma',*map(str,b['vertex_sigma_mm_ns']),'--random.seed',str(b['seed'])]
    execute(cmd,p)
    if not out.is_file() or out.stat().st_size==0:raise RuntimeError('Missing simulation output')
    done(p,sha256=digest(out),input_events=check_simulation(out,cfg['events']),mode='Geant4')


if __name__ == "__main__":
    parser = cli_parser(__doc__)
    parser.add_argument('--config', type=Path, default=REPO/'simulation/configs/electron_1GeV.json', help='Simulation configuration to snapshot')
    parser.add_argument('--sim-input', type=Path, help='Reuse an existing Simulation ROOT file without Geant4')
    run(simulate, parser)
