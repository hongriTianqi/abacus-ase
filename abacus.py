# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 10:31:30 2018

@author: shenzx

Modified on Wed Jun 03 22:00:00 2022
@author: Ji Yu-yang
"""

import warnings
import numpy as np

from ase import Atoms
from ase.utils import reader, writer
from ase.units import Bohr


def judge_exist_stru(stru=None):
    if stru is None:
        return False
    else:
        return True


def read_ase_stru(stru=None, coordinates_type="Cartesian"):
    if judge_exist_stru(stru):
        atoms_list = []
        atoms_position = []
        atoms_masses = []
        atoms_magnetism = []
        atoms_all = stru.get_chemical_symbols()

        # sort atoms according to atoms
        for atoms_all_name in atoms_all:
            temp = True
            for atoms_list_name in atoms_list:
                if atoms_all_name == atoms_list_name:
                    temp = False
                    break

            if temp:
                atoms_list.append(atoms_all_name)

        for atoms_list_name in atoms_list:
            atoms_position.append([])
            atoms_masses.append([])
            atoms_magnetism.append(0)

        # get position, masses, magnetism from ase atoms
        if coordinates_type == 'Cartesian':
            for i in range(len(atoms_list)):
                for j in range(len(atoms_all)):
                    if atoms_all[j] == atoms_list[i]:
                        atoms_position[i].append(list(
                            stru.get_positions()[j]))
                        atoms_masses[i] = stru.get_masses()[j]
                        atoms_magnetism[i] += np.linalg.norm(
                            stru.get_initial_magnetic_moments()[j])

        elif coordinates_type == 'Direct':
            for i in range(len(atoms_list)):
                for j in range(len(atoms_all)):
                    if atoms_all[j] == atoms_list[i]:
                        atoms_position[i].append(list(
                            stru.get_scaled_positions()[j]))
                        atoms_masses[i] = stru.get_masses()[j]
                        atoms_magnetism[i] += np.linalg.norm(
                            stru.get_initial_magnetic_moments()[j])

        else:
            raise ValueError("'coordinates_type' is ERROR,"
                             "please set to 'Cartesian' or 'Direct'")

        return atoms_list, atoms_masses, atoms_position, atoms_magnetism


def write_input_stru_core(fd,
                          stru=None,
                          pp=None,
                          basis=None,
                          offsite_basis=None,
                          coordinates_type="Cartesian",
                          atoms_list=None,
                          atoms_position=None,
                          atoms_masses=None,
                          atoms_magnetism=None,
                          fix=None,
                          set_vel=False,
                          set_mag=False):
    if not judge_exist_stru(stru):
        return "No input structure!"

    elif (atoms_list is None):
        return "Please set right atoms list"
    elif(atoms_position is None):
        return "Please set right atoms position"
    elif(atoms_masses is None):
        return "Please set right atoms masses"
    elif(atoms_magnetism is None):
        return "Please set right atoms magnetism"
    else:
        fd.write('ATOMIC_SPECIES\n')
        for i, elem in enumerate(atoms_list):
            pseudofile = pp[elem]
            temp1 = ' ' * (4-len(atoms_list[i]))
            temp2 = ' ' * (14-len(str(atoms_masses[i])))
            atomic_species = (atoms_list[i] + temp1
                              + str(atoms_masses[i]) + temp2
                              + pseudofile)

            fd.write(atomic_species)
            fd.write('\n')

        if basis is not None:
            fd.write('\n')
            fd.write('NUMERICAL_ORBITAL\n')
            for i, elem in enumerate(atoms_list):
                orbitalfile = basis[elem]
                fd.write(orbitalfile)
                fd.write('\n')

        if offsite_basis is not None:
            fd.write('\n')
            fd.write('ABFS_ORBITAL\n')
            for i, elem in enumerate(atoms_list):
                orbitalfile = offsite_basis[elem]
            fd.write(orbitalfile)
            fd.write('\n')

        fd.write('\n')
        fd.write('LATTICE_CONSTANT\n')
        fd.write('1.889726125 \n')
        fd.write('\n')

        fd.write('LATTICE_VECTORS\n')
        for i in range(3):
            for j in range(3):
                temp3 = str("{:0<12f}".format(
                    stru.get_cell()[i][j])) + ' ' * 3
                fd.write(temp3)
                fd.write('   ')
            fd.write('\n')
        fd.write('\n')

        fd.write('ATOMIC_POSITIONS\n')
        fd.write(coordinates_type)
        fd.write('\n')
        fd.write('\n')
        vel = stru.get_velocities()
        mag = stru.get_initial_magnetic_moments()
        for i in range(len(atoms_list)):
            fd.write(atoms_list[i])
            fd.write('\n')
            fd.write(str("{:0<12f}".format(float(atoms_magnetism[i]))))
            fd.write('\n')
            fd.write(str(len(atoms_position[i])))
            fd.write('\n')

            for j in range(len(atoms_position[i])):
                temp4 = str("{:0<12f}".format(
                    atoms_position[i][j][0])) + ' '
                temp5 = str("{:0<12f}".format(
                    atoms_position[i][j][1])) + ' '
                temp6 = str("{:0<12f}".format(
                    atoms_position[i][j][2])) + ' '
                sym_pos = temp4 + temp5 + temp6 + \
                    f'{fix[j][0]:.0f} {fix[j][1]:.0f} {fix[j][2]:.0f} '
                if set_vel:
                    sym_pos += f'v {vel[j][0]} {vel[j][1]} {vel[j][2]} '
                if set_mag:
                    if isinstance(mag[j], list):
                        sym_pos += f'mag {mag[j][0]} {mag[j][1]} {mag[j][2]} '
                    else:
                        sym_pos += f'mag {mag[j]} '
                fd.write(sym_pos)
                fd.write('\n')
            fd.write('\n')


@writer
def write_abacus(fd,
                 atoms=None,
                 pp=None,
                 basis=None,
                 offsite_basis=None,
                 scaled=False,
                 set_vel=False,
                 set_mag=False):

    if scaled:
        coordinates_type = 'Direct'
    else:
        coordinates_type = 'Cartesian'

    if not judge_exist_stru(atoms):
        return "No input structure!"

    else:
        (atoms_list,
         atoms_masses,
         atoms_position,
         atoms_magnetism) = read_ase_stru(atoms, coordinates_type)

        from ase.constraints import FixAtoms, FixCartesian
        fix_cart = np.ones([len(atoms), 3])
        if atoms.constraints:
            for constr in atoms.constraints:
                if isinstance(constr, FixAtoms):
                    fix_cart[constr.index] = [0, 0, 0]
                elif isinstance(constr, FixCartesian):
                    fix_cart[constr.a] = constr.mask

        write_input_stru_core(fd,
                              atoms,
                              pp,
                              basis,
                              offsite_basis,
                              coordinates_type,
                              atoms_list,
                              atoms_position,
                              atoms_masses,
                              atoms_magnetism,
                              fix_cart,
                              set_vel,
                              set_mag)


@reader
def read_abacus(fd, ase=True):
    """Read structure information from abacus structure file"""

    from ase.constraints import FixCartesian

    lines = fd.readlines()
    # initialize reading information
    temp = []
    for line in lines:
        line = line.strip()
        line = line.replace('\n', ' ')
        line = line.replace('\t', ' ')
        line = line.replace('//', ' ')
        line = line.replace('#', ' ')

        if len(line) != 0:
            temp.append(line)

    # print(temp)
    atom_species = 0
    for i in range(len(temp)):
        if temp[i] == 'NUMERICAL_ORBITAL':
            atom_species = i - 1
            break

    atom_symbol = []
    atom_mass = []
    atom_potential = []
    atom_number = []
    atom_magnetism = []
    atom_positions = []
    atom_appendix = []

    # get symbol, mass, potential
    for i in range(1, atom_species+1):
        atom_symbol.append(temp[i].split()[0])
        atom_mass.append(float(temp[i].split()[1]))
        atom_potential.append(temp[i].split()[2])
        atom_number.append(0)
        atom_magnetism.append(0)
        atom_positions.append([])
        atom_appendix.append([])

    # get abfs basis
    atom_basis = []
    atom_offsite_basis = []
    for i in range(atom_species+2, (atom_species+1) * 2):
        atom_basis.append(temp[i].split()[0])
    if 'ABFS_ORBITAL' in temp:
        scale = 3
        for i in range((atom_species+1) * 2 + 1, (atom_species+1) * 3):
            atom_offsite_basis.append(temp[i].split()[0])
    else:
        scale = 2

    # get lattice
    atom_lattice_scale = float(temp[(atom_species+1) * scale + 1].split()[0])
    atom_lattice = np.array(
        [[float(temp[(atom_species+1) * scale + 3 + i].split()[:3][j])
          for j in range(3)] for i in range(3)])

    # get coordinates type
    atom_coor = temp[(atom_species + 1) * scale + 7].split()[0]

    # get position,  atoms number, magnetism, appendix
    for i in range(atom_species):
        pos_start = (atom_species + 1) * scale + 8 + 3 * i
        for j in range(i):
            pos_start += atom_number[j]
        atom_it = atom_symbol.index(temp[pos_start].split()[0])
        atom_magnetism[atom_it] = float(temp[pos_start + 1].split()[0])
        atom_number[atom_it] = int(temp[pos_start + 2].split()[0])

        atom_positions[atom_it] = np.array(
            [[float(temp[pos_start + 3 + i].split()[:3][j])
              for j in range(3)] for i in range(atom_number[atom_it])])

        atom_appendix[atom_it] = [temp[pos_start + 3 + i].split()[3:]
                                  for i in range(atom_number[atom_it])]

    # Reset structure information and return results
    # and parse appendix: m, v, mag(magmom), (not support angle1, angle2)
    formula_symbol = ''
    formula_positions = []
    fix_cart = []
    velocities = []
    magnetism = []
    ci = -1  # fix ci atom

    def extract_appendix(start=0):
        xyz = ~np.array(atom_appendix[i][j][start:start+3]).astype('bool')
        vel = []
        mag = []
        if len(atom_appendix[i][j]) > start+3:
            if atom_appendix[i][j][start+3] in ['v', 'vel', 'velocity']:
                vel = list(map(float, atom_appendix[i][j][start+4:start+7]))
                if len(atom_appendix[i][j]) > start+7:
                    if atom_appendix[i][j][start+7] in ['mag', 'magmom']:
                        if len(atom_appendix[i][j]) == start+9:
                            warnings.warn(
                                "Non-colinear angle-settings are not yet supported for this interface.")
                            mag = float(atom_appendix[i][j][start+8])
                        else:
                            mag = list(
                                map(float, atom_appendix[i][j][start+8:start+11]))
            elif atom_appendix[i][j][start+3] in ['mag', 'magmom']:
                if len(atom_appendix[i][j]) == start+5 or len(atom_appendix[i][j][start+5]) in ['v', 'vel', 'velocity']:
                    mag = float(atom_appendix[i][j][start+4])
                    if atom_appendix[i][j][start+5] in ['v', 'vel', 'velocity']:
                        vel = list(
                            map(float, atom_appendix[i][j][start+8:start+11]))
                else:
                    mag = list(
                        map(float, atom_appendix[i][j][start+4:start+7]))
                    if atom_appendix[i][j][start+7] in ['v', 'vel', 'velocity']:
                        vel = list(
                            map(float, atom_appendix[i][j][start+8:start+11]))
        return xyz, vel, mag

    for i in range(atom_species):
        if atom_number[i] == 1:
            formula_symbol += atom_symbol[i]

        else:
            formula_symbol += atom_symbol[i] + str(atom_number[i])

        for j in range(atom_number[i]):
            formula_positions.append(atom_positions[i][j])

            # extract m
            # for ABACUS, 0: fix   1: move
            # for ASE,    0: move  1: fix
            xyz = np.array([0, 0, 0])
            ci += 1
            if atom_appendix[i][j][0] == 'm':
                xyz, vel, mag = extract_appendix(1)
            elif atom_appendix[i][j][0] in [0, 1]:
                xyz, vel, mag = extract_appendix(0)

            fix_cart.append(FixCartesian(ci, xyz))
            velocities.append(vel)
            if mag:
                magnetism.append(mag)
            else:
                magnetism.append(atom_magnetism[i])

    formula_cell = atom_lattice * atom_lattice_scale * Bohr

    if ase is True:
        if atom_coor == 'Direct':
            atoms = Atoms(symbols=formula_symbol,
                          cell=formula_cell,
                          scaled_positions=formula_positions,
                          pbc=True)

        elif atom_coor == 'Cartesian':
            atoms = Atoms(symbols=formula_symbol,
                          cell=formula_cell,
                          positions=formula_positions,
                          pbc=True)

        else:
            raise ValueError("atomic coordinate type is ERROR")

        if velocities:
            atoms.set_velocities(velocities)

        atoms.set_initial_magnetic_moments(magnetism)
        atoms.set_constraint(fix_cart)

        return atoms

    else:
        return (formula_symbol,
                formula_cell,
                formula_positions,
                atom_potential,
                atom_basis,
                atom_offsite_basis)

# Read ABACUS results


@reader
def read_abacus_out(fd, index=-1):
    # TODO: output for md, band, dos, ...
    cell = []
    energy = None
    force = None
    stress = None
    for line in fd:
        if 'Version' in line:
            ver = 'ABACUS version: '+ ' '.join(line.split()[1:])
        if "TOTAL ATOM NUMBER" in line:
            natom = int(line.split()[-1])
        # extract cell
        if "Volume (Bohr^3)" in line:
            V_b = float(line.split()[-1])
        if "Volume (A^3)" in line:
            V_a = float(line.split()[-1])
        if "Lattice vectors: (Cartesian coordinate: in unit of a_0)" in line:
            a_0 = pow(V_b/V_a, 1/3)*Bohr
            for i in range(3):
                ax, ay, az = fd.readline().split()
                cell.append([float(ax)*a_0, float(ay)*a_0, float(az)*a_0])
        # extract force
        if "TOTAL-FORCE (eV/Angstrom)" in line:
            force = np.zeros((natom, 3))
            for i in range(4):
                fd.readline()
            for i in range(natom):
                element, fx, fy, fz = fd.readline().split()
                force[i] = [float(fx), float(fy), float(fz)]
        # extract stress
        if "TOTAL-STRESS (KBAR)" in line:
            stress = np.zeros((3, 3))
            for i in range(3):
                fd.readline()
            for i in range(3):
                sx, sy, sz = fd.readline().split()
                stress[i] = [float(sx), float(sy), float(sz)]
        # extract energy
        if "final etot is" in line:
            energy = float(line.split()[-2])


if __name__ == '__main__':
    file = r'C:\Users\YY.Ji\Desktop\running_cell-relax.log'
    with open(file, 'r') as fd:
        read_abacus_out(file)
