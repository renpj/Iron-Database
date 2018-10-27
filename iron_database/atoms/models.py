from django.db import models
import dj_literature as literature

# Create your models here.

class Atoms(models.Model):
    #unique_id = models.CharField(max_length=100,unique=True,primary_key=True)
    # unique_id maybe trouble when combine two database
    ctime = models.DateTimeField('creation date', auto_now_add=True)
    mtime = models.DateTimeField('modification date', auto_now=True)
    pbc = models.CharField(max_length=40,default=json.dumps([False,False,False]))
    cell = models.CharField(max_length=400,default=json.dumps([[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]))
    atom = models.TextField(blank=True) # atom is a list of dict: keys=[position,magmom,charge,atomic_number,tag,momenta,mass]
    constraint = models.TextField(blank=True) # dict in ase
    info = models.TextField(blank=True)  # dict in ase
    l_optimized = models.BooleanField(default=False)
    l_ts = models.BooleanField(default=False) # is transition state?
    def to_ase(self):
        '''
        Construct ase.Atoms by append Atom.
        '''
        atoms=ase.Atoms(
            cell=json.loads(self.cell),
            pbc=json.loads(self.pbc),
            constraint=eval(self.constraint),  # maybe use dict in ase.constraint.dict2constraint
        )
        atom = json.loads(self.atom)
        for a in atom:
            item = ase.Atom(
                a['atomic_number'],
                a['position'],
                tag=a['tag'],
                momentum=a['momentum'],
                mass=a['mass'],
                charge=a['charge'],
                magmom=a['magmom'],
            )
            atoms.append(item)
        return atoms
    def import_ase(self,ase_atoms,save=True,l_ts=False,l_optimized=False):
        cell = json.dumps(ase_atoms.cell.tolist())
        pbc = json.dumps(ase_atoms.pbc.tolist())
        constraint = str(ase_atoms.constraints)
        info = json.dumps(ase_atoms.info)
        atom = []
        for a in ase_atoms:
            item = {
                'position':a.position.tolist(),
                'atomic_number':a.number,
                'mass':a.mass,
                'magmom':a.magmom,
                'charge':a.charge,
                'momentum':a.momentum.tolist(),
                'tag':a.tag,
            }
            atom.append(item)
        atoms_model = self(
            cell = cell,
            pbc = pbc,
            constraint = constraint,
            info = info,
            atom = json.dumps(atom),
            l_optimized=l_optimized,
            l_ts=l_ts,
        )
        if save:
            atoms_model.save()
        return atoms_model

    def __unicode__(self):
        atoms = self.ase()
        return atoms.get_chemical_formula()
        
class AtomsFile(models.Model):
    # store the original files as attachments
    # such as computational files
    atoms = models.ForeignKey(Atoms,on_delete='CASCADE')
    filename = models.CharField(maxlength=255)
    filetype = models.CharField(maxlength=255) # choice, input, output
    calculator = models.CharField(maxlength=255) # choice, from atoms.calc

class Surface(Atoms):
    # surface structure, indices, note
    # 
    indices = models.CharField(maxlength=20)
    cut_position = models.FloatField(default=0.0)

class Energy(models.Model):
    value = models.FloatField()
    UNIT_TYPE = (
        ('eV','eV'),
        ('kJ/mol','kJ/mol'),
        ('kcal/mol','kcal/mol'),
        ('Kelvin','Kelvin'),
        ('Ha','Hartree'),
        ('a.u.','Atomic Unit'),
    )
    unit = models.CharField(max_length=20,choices=UNIT_TYPE,default='eV')
    ctime = models.DateTimeField('creation date', auto_now_add=True)
    mtime = models.DateTimeField('modification date', auto_now=True)
    ENERGY_TYPE = (
        ('E0','Energy at 0K'),
        ('Ea','Transition state energy'),
        ('ZPE','Zero point Energy at 0K'),
        ('TS','Entropy*Temperature'),
        ('H','Enthalpy'),
        ('G','Gibbs Free Energy'),
        ('F','Helmholtz Free Energy'),
    )
    etype = models.CharField(max_length=200,choices=ENERGY_TYPE,default='E0')
    temperature = models.FloatField(default=0.0,help_text='Unit in Kelvin, default 0 K')
    pressure = models.FloatField(default=0.0,help_text='Unit in atm, default 0 atm')
    def unit2eV(self):
        if self.unit == 'eV':
            return self.value
        else:
            return convertor(self.value,self.unit,"eV")
    def __unicode__(self):
        return ':'.join([self.etype,'%.2f'%self.value]) + self.unit

class Source(models.Model):
    literature = models.ForeignKey(literature.models.Item, blank=True,null=True)
    doi = models.CharField(max_length=200,blank=True)
    SOURCETYPE_CHOICE=(
        ("theoretical","Theoretical"),
        ("experimental","Experimental"),
    )
    sourcetype = models.CharField(max_length=200,default="theoretical",choices=SOURCETYPE_CHOICE)

class AtomsSource(Source):
    atoms = models.ForeignKey(Atoms,on_delete='CASCADE')
class EnergySource(Source):
    energy = models.ForeignKey(Energy,on_delete='CASCADE')