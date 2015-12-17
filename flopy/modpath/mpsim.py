"""
mpsim module.  Contains the ModpathSim class. Note that the user can access
the ModpathSim class as `flopy.modpath.ModpathSim`.

Additional information for this MODFLOW/MODPATH package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/index.html?dis.htm>`_.

"""
import numpy as np
from ..pakbase import Package
from ..utils import Util2d, Util3d

class ModpathSim(Package):
    """
    MODPATH Simulation File Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.Modflow`) to which
        this package will be added.
    extension : string
        Filename extension (default is 'mpsim')


    Attributes
    ----------
    heading : str
        Text string written to top of package input file.

    Methods
    -------

    See Also
    --------

    Notes
    -----

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modpath.Modpath()
    >>> dis = flopy.modpath.ModpathSim(m)

    """
    def __init__(self, model, mp_name_file = 'mp.nam', mp_list_file = 'mp.list',
                 option_flags = [1, 2, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1],
                 ref_time = 0, ref_time_per_stp = [0, 1, 1.0], stop_time = None, group_ct = 1,
                 group_name = ['group_1'], group_placement = [[1, 1, 1, 0, 1, 1]], release_times = [[1, 1]],
                 group_region = [[1, 1, 1, 1, 1, 1]], mask_nlay = [1],
                 mask_layer = [1], mask_1lay = [1], face_ct = [1], ifaces = [[6, 1, 1]], part_ct = [[1, 1, 1]],
                 time_ct = 1, release_time_incr = 1, time_pts = [1],
                 particle_cell_cnt = [[2, 2, 2]], 
                 cell_bd_ct = 1, bud_loc = [[1, 1, 1, 1]], trace_id = 1, stop_zone = 1, zone = 1,
                 retard_fac = 1.0, retard_fcCB = 1.0, extension='mpsim'):
        
        # Call ancestor's init to set self.parent, extension, name and unit number
        Package.__init__(self, model, extension, 'MPSIM', 32) 
        nrow, ncol, nlay, nper = self.parent.mf.nrow_ncol_nlay_nper        

        self.heading1 = '# MPSIM for Modpath, generated by Flopy.'
        self.heading2 = '#'
        self.mp_name_file = '{}.{}'.format(model.name, 'mpnam')
        self.mp_list_file = '{}.{}'.format(model.name, 'mplst')
        options_list = ['SimulationType', 'TrackingDirection', 'WeakSinkOption', 'WeakSourceOption',
                        'ReferenceTimeOption', 'StopOption', 'ParticleGenerationOption', 'TimePointOption',
                        'BudgetOutputOption', 'ZoneArrayOption', 'RetardationOption',
                        'AdvectiveObservationsOption']
        self.option_flags = option_flags
        options_dict = dict(list(zip(options_list, option_flags)))
        self.options_dict = options_dict
        self.endpoint_file = '{}.{}'.format(model.name, 'mpend')
        self.pathline_file = '{}.{}'.format(model.name, 'mppth')
        self.time_ser_file = '{}.{}'.format(model.name, 'mp.tim_ser')
        self.advobs_file = '{}.{}'.format(model.name, '.mp.advobs')
        self.ref_time = ref_time 
        self.ref_time_per_stp = ref_time_per_stp
        self.stop_time = stop_time 
        self.group_ct = group_ct 
        self.group_name = group_name 
        self.group_placement = group_placement 
        self.release_times = release_times 
        self.group_region = group_region 
        self.mask_nlay = mask_nlay  
        self.mask_layer = mask_layer
        self.mask_1lay = mask_1lay
        self.face_ct = face_ct  
        self.ifaces = ifaces 
        self.part_ct = part_ct 
        self.strt_file = '{}.{}'.format(model.get_name(), 'loc')
        self.time_ct = time_ct  
        self.release_time_incr = release_time_incr	
        self.time_pts = time_pts
        self.particle_cell_cnt = particle_cell_cnt
        self.cell_bd_ct = cell_bd_ct 
        self.bud_loc = bud_loc  
        self.trace_file = '{}.{}'.format(model.get_name(), 'trace_file.txt')
        self.trace_id = trace_id 
        self.stop_zone = stop_zone 
        self.zone = zone  
        self.retard_fac = retard_fac 
        self.retard_fcCB = retard_fcCB
        
        #self.mask_nlay = Util3d(model,(nlay,nrow,ncol),np.int,\
                              #mask_nlay,name='mask_nlay',locat=self.unit_number[0])
        #self.mask_1lay = Util3d(model,(nlay,nrow,ncol),np.int,\
                              #mask_1lay,name='mask_1lay',locat=self.unit_number[0])
        #self.stop_zone = Util3d(model,(nlay,nrow,ncol),np.int,\
                              #stop_zone,name='stop_zone',locat=self.unit_number[0])
        #self.retard_fac = Util3d(model,(nlay,nrow,ncol),np.float32,\
                              #retard_fac,name='retard_fac',locat=self.unit_number[0])
        #self.retard_fcCB = Util3d(model,(nlay,nrow,ncol),np.float32,\
                              #retard_fcCB,name='retard_fcCB',locat=self.unit_number[0])

        self.parent.add_package(self)

    def write_file(self):
        """
        Write the package file

        Returns
        -------
        None

        """
        # item numbers and CamelCase variable names correspond to Modpath 6 documentation
        nrow, ncol, nlay, nper = self.parent.mf.nrow_ncol_nlay_nper
        
        f_sim = open(self.fn_path, 'w')
        # item 0
        f_sim.write('#{0:s}\n#{1:s}\n'.format(self.heading1,self.heading2))
        # item 1
        f_sim.write('{0:s}\n'.format(self.mp_name_file))
        # item 2
        f_sim.write('{0:s}\n'.format(self.mp_list_file))
        # item 3
        for i in range(12):
            f_sim.write('{0:4d}'.format(self.option_flags[i]))
        f_sim.write('\n')
        
        # item 4
        f_sim.write('{0:s}\n'.format(self.endpoint_file))
        # item 5
        if self.options_dict['SimulationType'] == 2:
            f_sim.write('{0:s}\n'.format(self.pathline_file))
        # item 6
        if self.options_dict['SimulationType'] == 3:
            f_sim.write('{0:s}\n'.format(self.time_ser_file))
        # item 7
        if self.options_dict['AdvectiveObservationsOption'] == 2 and self.option_dict['SimulationType'] == 3:
            f_sim.write('{0:s}\n'.format(self.advobs_file))
            
        # item 8
        if self.options_dict['ReferenceTimeOption'] == 1:
            f_sim.write('{0:f}\n'.format(self.ref_time))
        # item 9
        if self.options_dict['ReferenceTimeOption'] == 2:
            Period, Step, TimeFraction = self.ref_time_per_stp
            f_sim.write('{0:d} {1:d} {2:f}\n'.format(Period, Step, TimeFraction))

        # item 10
        if self.options_dict['StopOption'] == 3:
            f_sim.write('{0:f}\n'.format(self.stop_time))
            
        if self.options_dict['ParticleGenerationOption'] == 1:
            # item 11
            f_sim.write('{0:d}\n'.format(self.group_ct))
            for i in range(self.group_ct):
                # item 12
                f_sim.write('{0:s}\n'.format(self.group_name[i]))
                # item 13
                Grid, GridCellRegionOption, PlacementOption, ReleaseStartTime, ReleaseOption, CHeadOption = self.group_placement[i]
                f_sim.write('{0:d} {1:d} {2:d} {3:f} {4:d} {5:d}\n'.format(Grid, GridCellRegionOption, 
                                                                           PlacementOption, ReleaseStartTime, 
                                                                           ReleaseOption, CHeadOption))
                # item 14
                if ReleaseOption == 2:
                    ReleasePeriodLength, ReleaseEventCount = self.release_times[i]
                    f_sim.write('{0:f} {1:d}\n'.format(ReleasePeriodLength, ReleaseEventCount))
                # item 15
                if GridCellRegionOption == 1:
                    MinLayer, MinRow, MinColumn, MaxLayer, MaxRow, MaxColumn = self.group_region[i]
                    f_sim.write('{0:d} {1:d} {2:d} {3:d} {4:d} {5:d}\n'.format(MinLayer+1, MinRow+1, MinColumn+1, 
                                                                               MaxLayer+1, MaxRow+1, MaxColumn+1))
                # item 16
                if GridCellRegionOption == 2:
                    f_sim.write(self.mask_nlay[i].get_file_entry())                        
                # item 17
                if GridCellRegionOption == 3:
                    f_sim.write('{0:s}\n'.format(self.mask_layer[i]))            
                # item 18
                    f_sim.write(self.mask_1lay[i].get_file_entry())
                # item 19
                if PlacementOption == 1:
                    f_sim.write('{0:d}\n'.format(self.face_ct[i]))
                    # item 20
                    for j in range(self.face_ct[i]):
                        IFace, ParticleRowCount, ParticleColumnCount = self.ifaces[i][j]
                        f_sim.write('{0:d} {1:d} {2:d} \n'.format(IFace, ParticleRowCount, ParticleColumnCount))
                # item 21
                if PlacementOption == 2:
                    ParticleLayerCount, ParticleRowCount, ParticleColumnCount = self.particle_cell_cnt[i]
                    f_sim.write('{0:d} {1:d} {2:d} \n'.format(ParticleLayerCount, ParticleRowCount, ParticleColumnCount))            

        # item 22
        if self.options_dict['ParticleGenerationOption'] == 2:
            f_sim.write('{0:s}\n'.format(self.strt_file))
            
        if self.options_dict['TimePointOption'] != 1:
            # item 23
            if self.options_dict['TimePointOption'] == 2 or self.options_dict['TimePointOption'] == 3:
                f_sim.write('{0:d}\n'.format(self.time_ct))
            # item 24
            if self.options_dict['TimePointOption'] == 2:
                f_sim.write('{0:f}\n'.format(self.release_time_incr))
            # item 25
            if self.options_dict['TimePointOption'] == 3:
                for r in range(self.time_ct):
                    f_sim.write('{0:f}\n'.format(self.time_pts[r]))
                
        if self.options_dict['BudgetOutputOption'] != 1 or self.options_dict['BudgetOutputOption'] != 2:
            # item 26
            if self.options_dict['BudgetOutputOption'] == 3:
                f_sim.write('{0:d}\n'.format(self.cell_bd_ct))
                # item 27
                for k in range(self.cell_bd_ct):
                    Grid, Layer, Row, Column = self.bud_loc[k]
                    f_sim.write('{0:d} {1:d} {2:d} {3:d} \n'.format(Grid, Layer+1, Row+1, Column+1))
            if self.options_dict['BudgetOutputOption'] == 4:
                # item 28
                f_sim.write('{0:s}\n'.format(self.trace_file))
                # item 29
                f_sim.write('{0:s}\n'.format(self.trace_id))
                
        if self.options_dict['ZoneArrayOption'] != 1:
            # item 30
            f_sim.write('{0:s}\n'.format(self.stop_zone))
            # item 31
            f_sim.write(self.stop_zone.get_file_entry())
            
        if self.options_dict['RetardationOption'] != 1:
            # item 32
            f_sim.write(self.retard_fac.get_file_entry())
            # item 33
            f_sim.write(self.retard_fcCB.get_file_entry())

        f_sim.close()
