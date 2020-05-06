# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from michael_shafferContigFilter.michael_shafferContigFilterImpl import michael_shafferContigFilter
from michael_shafferContigFilter.michael_shafferContigFilterServer import MethodContext
from michael_shafferContigFilter.authclient import KBaseAuth as _KBaseAuth

from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.WorkspaceClient import Workspace


class michael_shafferContigFilterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('michael_shafferContigFilter'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'michael_shafferContigFilter',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = michael_shafferContigFilter(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa
        cls.prepareTestData()

    @classmethod
    def prepareTestData(cls):
        """This function creates an assembly object for testing"""
        fasta_content = '>seq1 something soemthing asdf\n' \
                        'agcttttcat\n' \
                        '>seq2\n' \
                        'agctt\n' \
                        '>seq3\n' \
                        'agcttttcatgg'

        filename = os.path.join(cls.scratch, 'test1.fasta')
        with open(filename, 'w') as f:
            f.write(fasta_content)
        assemblyUtil = AssemblyUtil(cls.callback_url)
        cls.assembly_ref = assemblyUtil.save_assembly_from_fasta({
            'file': {'path': filename},
            'workspace_name': cls.wsName,
            'assembly_name': 'TestAssembly'
        })

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_run_michael_shafferContigFilter_ok(self):
        # call your implementation
        ret = self.serviceImpl.run_michael_shafferContigFilter(self.ctx,
                                                {'workspace_name': self.wsName,
                                                 'assembly_input_ref': self.assembly_ref,
                                                 'min_length': 10
                                                 })

        # Validate the returned data
        self.assertEqual(ret[0]['n_initial_contigs'], 3)
        self.assertEqual(ret[0]['n_contigs_removed'], 1)
        self.assertEqual(ret[0]['n_contigs_remaining'], 2)

    def test_run_michael_shafferContigFilter_min_len_negative(self):
        with self.assertRaisesRegex(ValueError, 'min_length parameter cannot be negative'):
            self.serviceImpl.run_michael_shafferContigFilter(self.ctx,
                                              {'workspace_name': self.wsName,
                                               'assembly_input_ref': '1/fake/3',
                                               'min_length': '-10'})

    def test_run_michael_shafferContigFilter_min_len_parse(self):
        with self.assertRaisesRegex(ValueError, 'Cannot parse integer from min_length parameter'):
            self.serviceImpl.run_michael_shafferContigFilter(self.ctx,
                                              {'workspace_name': self.wsName,
                                               'assembly_input_ref': '1/fake/3',
                                               'min_length': 'ten'})

    def test_run_michael_shafferContigFilter_max(self):
        ref = '79/16/1'
        result = self.serviceImpl.run_michael_shafferContigFilter_max(self.ctx, {
            'workspace_name': self.wsName,
            'assembly_ref': ref,
            'max_length': 1000000
        })

    def test_invalid_params_ContigFilter_max(self):
        impl = self.serviceImpl
        ctx = self.ctx
        ws = self.wsName
        # missing assembly ref
        with self.assertRaises(ValueError):
            impl.run_michael_shafferContigFilter(ctx, {'workspace_name': ws, 'max_length': 1000000})
            # assembly ref is wrong type
        with self.assertRaises(ValueError):
            impl.run_michael_shafferContigFilter(ctx,
                                                 {'workspace_name': ws, 'assembly_ref': 123, 'max_length': 100000})
        # missing max length
        with self.assertRaises(ValueError):
            impl.run_michael_shafferContigFilter(ctx, {'workspace_name': ws, 'assembly_ref': 'x'})
        # max length is negative
        with self.assertRaises(ValueError):
            impl.run_michael_shafferContigFilter(ctx, {'workspace_name': ws, 'assembly_ref': 'x', 'max_length': -1})
        # max length is wrong type
        with self.assertRaises(ValueError):
            impl.run_michael_shafferContigFilter(ctx, {'workspace_name': ws, 'assembly_ref': 'x',
                                                       'max_length': 'Hello World'})

    def test_run_michael_shafferContigFilter_test_max(self):
        ref = "79/16/1"
        params = {'workspace_name': self.wsName,
                  'assembly_ref': ref,
                  'max_length': 600000}
        result = self.serviceImpl.run_michael_shafferContigFilter_max(self.ctx, params)
        self.assertEqual(result[0]['n_total'], 2)
        self.assertEqual(result[0]['n_kept'], 1)
        self.assertTrue(len(result[0]['filtered_assembly_ref']))
        self.assertTrue(len(result[0]['report_name']))
        self.assertTrue(len(result[0]['report_ref']))
