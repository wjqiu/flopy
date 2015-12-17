"""
mfghb module.  Contains the ModflowEvt class. Note that the user can access
the ModflowEvt class as `flopy.modflow.ModflowEvt`.

Additional information for this MODFLOW package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/index.html?evt.htm>`_.

"""
import sys
import numpy as np
from ..pakbase import Package
from flopy.utils.util_array import Transient2d, Util2d
from flopy.modflow.mfparbc import ModflowParBc as mfparbc


class ModflowEvt(Package):
    """
    MODFLOW Evapotranspiration Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.ModflowEvt`) to which
        this package will be added.
    ipakcb : int
        A flag that is used to determine if cell-by-cell budget data should be
        saved. If ipakcb is non-zero cell-by-cell budget data will be saved.
        (default is 0).
    nevtop : int
        is the recharge option code.
        1: ET is calculated only for cells in the top grid layer
        2: ET to layer defined in ievt
        3: ET to highest active cell (default is 3).
    surf : float or filename or ndarray or dict keyed on kper (zero-based)
        is the ET surface elevation. (default is 0.0, which is used for all
        stress periods).
    evtr: float or filename or ndarray or dict keyed on kper (zero-based)
        is the maximum ET flux (default is 1e-3, which is used for all
        stress periods).
    exdp : float or filename or ndarray or dict keyed on kper (zero-based)
        is the ET extinction depth (default is 1.0, which is used for all
        stress periods).
    ievt : int or filename or ndarray or dict keyed on kper (zero-based)
        is the layer indicator variable (default is 1, which is used for all
        stress periods).
    extension : string
        Filename extension (default is 'evt')
    unitnumber : int
        File unit number (default is 22).

    Attributes
    ----------

    Methods
    -------

    See Also
    --------

    Notes
    -----
    Parameters are not supported in FloPy.

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modflow.Modflow()
    >>> evt = flopy.modflow.ModflowEvt(m, nevtop=3, evtr=1.2e-4)

    """
    def __init__(self, model, nevtop=3, ipakcb=0, surf=0., evtr=1e-3, exdp=1., ievt=1, 
                 extension ='evt', unitnumber=22, external=True):
        # Call ancestor's init to set self.parent, extension, name and unit number
        Package.__init__(self, model, extension, 'EVT', unitnumber)
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        self.heading = '# EVT for MODFLOW, generated by Flopy.'
        self.url = 'evt.htm'
        self.nevtop = nevtop
        if ipakcb != 0:
            self.ipakcb = 53
        else:
            self.ipakcb = 0  # 0: no cell by cell terms are written
        self.external = external
        if self.external is False:
            load = True
        else:
            load = model.load            

        self.surf = Transient2d(model, (nrow, ncol), np.float32,
                                 surf, name='surf')
        self.evtr = Transient2d(model, (nrow, ncol), np.float32,
                                 evtr, name='etvr')
        self.exdp = Transient2d(model, (nrow, ncol), np.float32,
                                 exdp, name='exdp')
        self.ievt = Transient2d(model, (nrow, ncol), np.int,
                                 ievt, name='ievt')
        self.np = 0
        self.parent.add_package(self)

    def ncells(self):
        # Returns the  maximum number of cells that have 
        # evapotranspiration (developed for MT3DMS SSM package)
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        return (nrow * ncol)

    def write_file(self):
        """
        Write the package file.

        Returns
        -------
        None

        """
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        f_evt = open(self.fn_path, 'w')        
        f_evt.write('{0:s}\n'.format(self.heading))        
        f_evt.write('{0:10d}{1:10d}\n'.format(self.nevtop,self.ipakcb))
        for n in range(nper):
            insurf,surf = self.surf.get_kper_entry(n)
            inevtr,evtr = self.evtr.get_kper_entry(n)
            inexdp,exdp = self.exdp.get_kper_entry(n)
            inievt,ievt = self.ievt.get_kper_entry(n)
            comment = 'Evapotranspiration  dataset 5 for stress period ' +\
                      str(n + 1)
            f_evt.write('{0:10d}{1:10d}{2:10d}{3:10d} # {4:s}\n'
                        .format(insurf, inevtr, inexdp, inievt, comment))
            if (insurf >= 0):
                f_evt.write(surf)
            if (inevtr >= 0):
                f_evt.write(evtr)
            if (inexdp >= 0):
                f_evt.write(exdp)
            if self.nevtop == 2 and inievt >= 0:
                f_evt.write(ievt)
        f_evt.close()

    @staticmethod
    def load(f, model, nper=None, ext_unit_dict=None):
        """
        Load an existing package.

        Parameters
        ----------
        f : filename or file handle
            File to load.
        model : model object
            The model object (of type :class:`flopy.modflow.mf.Modflow`) to
            which this package will be added.
        nper : int
            The number of stress periods.  If nper is None, then nper will be
            obtained from the model object. (default is None).
        ext_unit_dict : dictionary, optional
            If the arrays in the file are specified using EXTERNAL,
            or older style array control records, then `f` should be a file
            handle.  In this case ext_unit_dict is required, which can be
            constructed using the function
            :class:`flopy.utils.mfreadnam.parsenamefile`.

        Returns
        -------
        evt : ModflowEvt object
            ModflowEvt object.

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow()
        >>> evt = flopy.modflow.mfevt.load('test.evt', m)

        """
        if model.verbose:
            sys.stdout.write('loading evt package file...\n')

        if not hasattr(f, 'read'):
            filename = f
            f = open(filename, 'r')
        # Dataset 0 -- header
        while True:
            line = f.readline()
            if line[0] != '#':
                break
        npar = 0
        if "parameter" in line.lower():
            raw = line.strip().split()
            npar = int(raw[1])
            if npar > 0:
                if model.verbose:
                    print('  Parameters detected. Number of parameters = ', npar)
            line = f.readline()
        # Dataset 2
        t = line.strip().split()
        nevtop = int(t[0])
        ipakcb = 0
        try:
            if int(t[1]) != 0:
                model.add_pop_key_list(int(t[1]))
                ipakcb = 53
        except:
            pass

        # Dataset 3 and 4 - parameters data
        pak_parms = None
        if npar > 0:
            pak_parms = mfparbc.loadarray(f, npar, model.verbose)


        if nper is None:
            nrow, ncol, nlay, nper = model.get_nrow_ncol_nlay_nper()

        # Read data for every stress period
        surf = {}
        evtr = {}
        exdp = {}
        ievt = {}
        current_surf = []
        current_evtr = []
        current_exdp = []
        current_ievt = []
        for iper in range(nper):
            line = f.readline()
            t = line.strip().split()
            insurf = int(t[0])
            inevtr = int(t[1])
            inexdp = int(t[2])
            if (nevtop == 2):
              inievt = int(t[3])
            if insurf >= 0:
                if model.verbose:
                    print('   loading surf stress period {0:3d}...'.format(iper+1))
                t = Util2d.load(f, model, (nrow,ncol), np.float32, 'surf',
                                 ext_unit_dict)
                current_surf = t
            surf[iper] = current_surf

            if inevtr >= 0:
                if npar == 0:
                    if model.verbose:
                        print('   loading evtr stress period {0:3d}...'.format(iper+1))
                    t = Util2d.load(f, model, (nrow,ncol), np.float32, 'evtr',
                                     ext_unit_dict)
                else:
                    parm_dict = {}
                    for ipar in range(inevtr):
                        line = f.readline()
                        t = line.strip().split()
                        pname = t[0].lower()
                        try:
                            c = t[1].lower()
                            if c in pak_parms.bc_parms:
                                iname = c
                            else:
                                iname = 'static'
                        except:
                            iname = 'static'
                        parm_dict[pname] = iname
                    t = mfparbc.parameter_bcfill(model, (nrow, ncol), parm_dict, pak_parms)


                current_evtr = t
            evtr[iper] = current_evtr
            if inexdp >= 0:
                if model.verbose:
                    print('   loading exdp stress period {0:3d}...'.format(iper+1))
                t = Util2d.load(f, model, (nrow, ncol), np.float32, 'exdp',
                                 ext_unit_dict)
                current_exdp = t
            exdp[iper] = current_exdp
            if nevtop == 2:
                if inievt >= 0:
                    if model.verbose:
                        print('   loading ievt stress period {0:3d}...'.format(
                            iper+1))
                    t = Util2d.load(f, model, (nrow, ncol), np.int32, 'ievt',
                                     ext_unit_dict)
                    current_ievt = t
                ievt[iper] = current_ievt

        # create evt object
        args = {}
        if ievt:
            args["ievt"] = ievt
        if nevtop:
            args["nevtop"] = nevtop
        if evtr:
            args["evtr"] = evtr
        if surf:
            args["surf"] = surf
        if exdp:
            args["exdp"] = exdp
        args["ipakcb"] = ipakcb
        evt = ModflowEvt(model, **args)
        # return evt object
        return evt
