# Need to import path to test/fixtures and test/scripts/
# Ex : export PYTHONPATH='$PATH:/root/test/fixtures/:/root/test/scripts/'
# 
# To run tests, you can do 'python -m testtools.run tests'. To run specific tests,
# You can do 'python -m testtools.run -l tests'
# Set the env variable PARAMS_FILE to point to your ini file. Else it will try to pick params.ini in PWD
# 
import os
import time    
from novaclient import client as mynovaclient
from novaclient import exceptions as novaException
import fixtures
import testtools
import unittest
import re
import socket    

from contrail_test_init import *
from vn_test import *
from quantum_test import *
from vnc_api_test import *
from nova_test import *
from vm_test import *
from connections import ContrailConnections
from floating_ip import *
from policy_test import *
from multiple_vn_vm_test import *
from contrail_fixtures import *
from tcutils.wrappers import preposttest_wrapper
from testresources import ResourcedTestCase
from sanity_resource import SolnSetupResource
#from analytics_tests import *
sys.path.append(os.path.realpath('tcutils/pkgs/Traffic'))
from traffic.core.stream import Stream
from traffic.core.profile import create, ContinuousProfile,StandardProfile, BurstProfile
from traffic.core.helpers import Host
from traffic.core.helpers import Sender, Receiver
from servicechain.config import ConfigSvcChain
from servicechain.verify import VerifySvcChain

#class AnalyticsTestSanity(testtools.TestCase, fixtures.TestWithFixtures, ResourcedTestCase ):
class AnalyticsTestSanity(testtools.TestCase, ResourcedTestCase, ConfigSvcChain , VerifySvcChain):
    
    resources = [('base_setup', SolnSetupResource)]
    def __init__(self, *args, **kwargs):
        testtools.TestCase.__init__(self, *args, **kwargs)
        self.res= SolnSetupResource.getResource()
        self.inputs= self.res.inputs
        self.connections= self.res.connections
        self.logger= self.res.logger
        self.nova_fixture= self.res.nova_fixture
        self.analytics_obj=self.connections.analytics_obj
        self.vnc_lib = self.connections.vnc_lib
#        self.svc_obj=VerifySvcFirewall() 
    def __del__(self):
        print "Deleting test_with_setup now"
        SolnSetupResource.finishedWith(self.res)
    
    def setUp(self):
        super (AnalyticsTestSanity, self).setUp()
        if 'PARAMS_FILE' in os.environ :
            self.ini_file= os.environ.get('PARAMS_FILE')
        else:
            self.ini_file= 'params.ini'
    
    def tearDown(self):
        print "Tearing down test"
        super (AnalyticsTestSanity, self).tearDown()
        SolnSetupResource.finishedWith(self.res)
    
    def runTest(self):
        pass
    #end runTest

#    @preposttest_wrapper
#    def test_collector_uve(self):
#        '''Test to validate collector uve.
#        '''
#        assert self.analytics_obj.verify_collector_uve()
#        return True
#    #end test_collector_uve
#    
#    @preposttest_wrapper
#    def test_vrouter_uve(self):
#        '''Test to validate vrouter uve xmpp connections.
#        '''
#        assert self.analytics_obj.verify_vrouter_xmpp_connections()
#        return True
    #end test_vrouter_uve

    @preposttest_wrapper
    def test_vn_uve_tiers(self):
        '''Test to validate vn uve receives uve message from api-server and Agent.
        '''
        vn_list=[self.res.vn1_fixture.vn_fq_name,self.res.vn2_fixture.vn_fq_name,self.res.fvn_fixture.vn_fq_name]
        for vn in vn_list:
            assert self.analytics_obj.verify_vn_uve_tiers(vn_fq_name=vn)
        return True
    

    @preposttest_wrapper
    def test_vn_uve_routing_instance(self):
        '''Test to validate routing instance in vn uve.
        '''
        vn_list=[self.res.vn1_fixture.vn_fq_name,self.res.vn2_fixture.vn_fq_name,self.res.fvn_fixture.vn_fq_name]
        for vn in vn_list:
            assert self.analytics_obj.verify_vn_uve_ri(vn_fq_name=vn)
        return True
    

#    @preposttest_wrapper
#    def test_vn_uve_vm_list(self):
#        '''Test to validate vm list in vn uve.
#        '''
#        vm_uuid_lst=[]
#        vn_uuid_dct={}    
#        vn_list=[self.res.vn1_name,self.res.vn2_name,self.res.fip_vn_name]
#        #getting all the vm uuid
#        vn1_vmobj_list_uuid=[self.res.vn1_vm1_fixture.vm_id,self.res.vn1_vm2_fixture.vm_id,self.res.vn1_vm3_fixture.vm_id,self.res.vn1_vm4_fixture.vm_id]
#        vm_uuid_lst.append(vn1_vmobj_list_uuid)
#        vn2_vmobj_list_uuid=[self.res.vn2_vm1_fixture.vm_id,self.res.vn2_vm2_fixture.vm_id]
#        vm_uuid_lst.append(vn2_vmobj_list_uuid)
#        fvn_vmobj_list_uuid=[self.res.fvn_vm1_fixture.vm_id]
#        vm_uuid_lst.append(fvn_vmobj_list_uuid)
#        vn_uuid_dct=dict(zip(vn_list,vm_uuid_lst))
#        
#        for k in vn_uuid_dct:
#            assert self.analytics_obj.verify_vm_list(vn=k,vm_uuid_lst=vn_uuid_dct[k])
#        return True
    

    @preposttest_wrapper
    def test_vrouter_uve_vm_on_vm_create(self):
        '''Test to validate vm list,connected networks and tap interfaces in vrouter uve.
        '''
#        vn_list=[self.res.vn1_name,self.res.vn2_name,self.res.fip_vn_name]
        vn_list=[self.res.vn1_fixture.vn_fq_name,self.res.vn2_fixture.vn_fq_name,self.res.fvn_fixture.vn_fq_name]
        vm_fixture_list=[self.res.vn1_vm1_fixture,self.res.vn1_vm2_fixture,self.res.vn1_vm3_fixture,self.res.vn1_vm4_fixture,self.res.vn2_vm1_fixture,
                            self.res.vn2_vm2_fixture,self.res.fvn_vm1_fixture]
        
        
        for vm_fixture in vm_fixture_list:
            assert vm_fixture.verify_on_setup()
            vm_uuid=vm_fixture.vm_id
            vm_node_ip= vm_fixture.inputs.host_data[vm_fixture.nova_fixture.get_nova_host_of_vm(vm_fixture.vm_obj)]['host_ip']
            vn_of_vm= vm_fixture.vn_fq_name
            vm_host=vm_fixture.inputs.host_data[vm_node_ip]['name']
            interface_name=vm_fixture.agent_inspect[vm_node_ip].get_vna_tap_interface_by_vm(vm_id= vm_uuid)[0]['config_name']
            self.logger.info("expected tap interface of vm uuid %s is %s"%(vm_uuid,interface_name))
            self.logger.info("expected virtual netowrk  of vm uuid %s is %s"%(vm_uuid,vn_of_vm))
            assert self.analytics_obj.verify_vm_list_in_vrouter_uve(vm_uuid=vm_uuid,vn_fq_name=vn_of_vm,vrouter=vm_host,tap=interface_name)
        
        return True
    
    @preposttest_wrapper
    def test_virtual_machine_uve_vm_tiers(self):
        '''Test to validate virtual machine uve tiers - should be UveVirtualMachineConfig and UveVirtualMachineAgent.
        '''
        vm_uuid_list=[self.res.vn1_vm1_fixture.vm_id,self.res.vn1_vm2_fixture.vm_id,self.res.vn1_vm3_fixture.vm_id,
                                self.res.vn1_vm4_fixture.vm_id,self.res.vn2_vm1_fixture.vm_id,
                                self.res.vn2_vm2_fixture.vm_id,self.res.fvn_vm1_fixture.vm_id]
        for uuid in vm_uuid_list:
            assert self.analytics_obj.verify_vm_uve_tiers(uuid=uuid)
        return True
        
        

#    @preposttest_wrapper
#    def test_virtual_machine_uve_and_other_uve_cross_verification(self):
#        '''Test to validate virtual machine uve and cross verification with vrouter uve and vn uve.
#        '''
#        vm_uuid_list=[self.res.vn1_vm1_fixture.vm_id,self.res.vn1_vm2_fixture.vm_id,self.res.vn1_vm3_fixture.vm_id,
#                                self.res.vn1_vm4_fixture.vm_id,self.res.vn2_vm1_fixture.vm_id,
#                                self.res.vn2_vm2_fixture.vm_id,self.res.fvn_vm1_fixture.vm_id]
#        for uuid in vm_uuid_list:
#            vm_intf=self.analytics_obj.get_ops_vm_uve_interface(uuid=uuid)
#            for intf in vm_intf:
#                virtual_network=intf['virtual_network']
#                vn=virtual_network.split(':')[-1:][0]
#                ip_address=intf['ip_address']
#                intf_name=intf['name']
#                self.logger.info("vm uve shows interface as %s"%(intf_name))
#                self.logger.info("vm uve shows ip address as %s"%(ip_address))
#                self.logger.info("vm uve shows virtual netowrk as %s"%(virtual_network))
#                #import pdb;pdb.set_trace()
#            #Verify the vm is present in the vm uve specified vn
#                assert self.analytics_obj.verify_vn_uve_for_vm(vn=vn,vm=uuid)
#            #verify vm present in the vrouter specified in the vm uve
#                compute=self.analytics_obj.get_ops_vm_uve_vm_host(uuid)
#                self.logger.info("vm uve shows vrouter as %s"%(compute))
#                assert self.analytics_obj.verify_vm_list_in_vrouter_uve(vm_uuid=uuid,vrouter=compute)
#        return True
#    

#    @preposttest_wrapper
#    def test_delete_vm_and_verify_vm_uve_and_uve_cross_verification(self):
#        '''Test to validate vn uve,vm uve and vrouter uve when vm/vn deleted.
#        '''
#        #creating vm
#        vm1_name='vm_mine'
#        vn_name='vn22'
#        vn_subnets=['22.1.1.0/24']
#        vn_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,
#                     vn_name=vn_name, inputs= self.inputs, subnets= vn_subnets))
#        vn_obj= vn_fixture.obj
#        vm1_fixture= self.useFixture(VMFixture(connections= self.connections,
#                vn_obj=vn_obj, vm_name= vm1_name, project_name= self.inputs.project_name))
#        #getting vm uuid
#        assert vm1_fixture.verify_on_setup()
#        vm_uuid=vm1_fixture.vm_id
#        
#        vm_intf=self.analytics_obj.get_ops_vm_uve_interface(self.inputs.collector_ips[0],uuid=vm_uuid)
#        for intf in vm_intf:
#            virtual_network=intf['virtual_network']
#            vn=virtual_network.split(':')[-1:][0]
#            ip_address=intf['ip_address']
#            intf_name=intf['name']
#            self.logger.info("vm uve shows interface as %s"%(intf_name))
#            self.logger.info("vm uve shows ip address as %s"%(ip_address))
#            self.logger.info("vm uve shows virtual netowrk as %s"%(virtual_network))
#                #import pdb;pdb.set_trace()
#            #Verify the vm is present in the vm uve specified vn
#            assert self.analytics_obj.verify_vn_uve_for_vm(vn=vn,vm=vm_uuid)
#            #verify vm present in the vrouter specified in the vm uve
#            compute=self.analytics_obj.get_ops_vm_uve_vm_host(self.inputs.collector_ips[0],vm_uuid)
#            self.logger.info("vm uve shows vrouter as %s"%(compute))
#            assert self.analytics_obj.verify_vm_list_in_vrouter_uve(vm_uuid=vm_uuid,vrouter=compute)
#        #deleting vm and verifyinng that vm uve does not return anything
#        vm1_fixture.cleanUp()
##        vm1_fixture.nova_fixture.delete_vm(vm1_fixture.vm_obj)
#        time.sleep(10)
#        #Verifying the uve for vm,vn,vrouter that vm info deleted
##        vm_uve_output=self.analytics_obj.get_vm_uve(self.inputs.collector_ips[0],vm_uuid)
##        import pdb;pdb.set_trace()    
##        self.logger.info("vm uve after delete of vm %s"%(vm_uve_output))
##        assert (not self.analytics_obj.get_vm_uve(self.inputs.collector_ips[0],vm_uuid)) 
##        assert (not self.analytics_obj.verify_vm_list_in_vrouter_uve(vrouter=compute,vm_uuid=vm_uuid))
##        assert (not self.analytics_obj.verify_vn_uve_for_vm(vn=vn_name,vm=vm_uuid))
#        return True
        
    
    #end test_vn_uve_tiers
    
#
#
#    @preposttest_wrapper
#    def test_floating_ip(self):
#        '''Test to validate floating-ip Assignment to a VM. It creates a VM, assigns a FIP to it and pings to a IP in the FIP VN.
#        '''
#        result= True
#        fip_pool_name= 'some-pool1'
#        fvn_name= self.res.fip_vn_name
#        fvn_fixture= self.res.fvn_fixture
#        vn1_fixture= self.res.vn1_fixture
#        vn1_vm1_fixture= self.res.vn1_vm1_fixture
#        fvn_vm1_fixture= self.res.fvn_vm1_fixture
#        fvn_subnets= self.res.fip_vn_subnets
#        vm1_name= self.res.vn1_vm1_name
#        vn1_name= self.res.vn1_name
#        vn1_subnets= self.res.vn1_subnets
#        assert fvn_fixture.verify_on_setup()
#        assert vn1_fixture.verify_on_setup()
#        assert vn1_vm1_fixture.verify_on_setup()
#        assert fvn_vm1_fixture.verify_on_setup()
#
#        fip_fixture= self.useFixture(FloatingIPFixture( project_name= self.inputs.project_name, inputs = self.inputs,
#                    connections= self.connections, pool_name = fip_pool_name, vn_id= fvn_fixture.vn_id ))
#        assert fip_fixture.verify_on_setup()
#        fip_id= fip_fixture.create_and_assoc_fip( fvn_fixture.vn_id, vn1_vm1_fixture.vm_id)
#        assert fip_fixture.verify_fip( fip_id, vn1_vm1_fixture, fvn_fixture )
#        if not vn1_vm1_fixture.ping_with_certainty( fvn_vm1_fixture.vm_ip ):
#            result = result and False
#        fip_fixture.disassoc_and_delete_fip(fip_id)
#        if not result :
#            self.logger.error('Test to ping between VMs %s and %s' %(vn1_vm1_name, fvn_vm1_name))
#            assert result
#        return True
#    #end test_floating_ip
#
#    @preposttest_wrapper
#    def test_policy_to_deny(self):
#        ''' Test to validate that with policy having rule to disable icmp within the VN, ping between VMs should fail
#
#        '''
#        vn1_name= self.res.vn1_name
#        vn1_subnets= self.res.vn1_subnets
#        policy_name= 'policy1'
#        rules= [
#            {
#               'direction'     : '<>', 'simple_action' : 'deny',
#               'protocol'      : '1',
#               'source_network': vn1_name,
#               'dest_network'  : vn1_name,
#             },
#                ]
#        policy_fixture= self.useFixture( PolicyFixture( policy_name= policy_name, rules_list= rules, inputs= self.inputs,
#                                    connections= self.connections ))
#        vn1_fixture= self.res.vn1_fixture
#        vn1_fixture.bind_policies([policy_fixture.policy_fq_name], vn1_fixture.vn_id)
#        self.addCleanup( vn1_fixture.unbind_policies, vn1_fixture.vn_id, [policy_fixture.policy_fq_name] )
#        assert vn1_fixture.verify_on_setup()
#
#        vn1_vm1_name= self.res.vn1_vm1_name
#        vn1_vm2_name= self.res.vn1_vm2_name
#        vm1_fixture= self.res.vn1_vm1_fixture
#        assert vm1_fixture.verify_on_setup()
#        vm2_fixture= self.res.vn1_vm2_fixture
#        assert vm2_fixture.verify_on_setup()
#        self.nova_fixture.wait_till_vm_is_up( vm1_fixture.vm_obj )
#        self.nova_fixture.wait_till_vm_is_up( vm2_fixture.vm_obj )
#        assert not vm1_fixture.ping_to_ip( vm2_fixture.vm_ip )
#        return True
#
#    #end test_policy
#
#    @preposttest_wrapper
#    def test_vrouter_uve_for_active_flow(self):
#        ''' Test to validate active flow in vrouter uve
#
#        '''
#        vn1_name= self.res.vn1_name
#        vn1_subnets= self.res.vn1_subnets
#        vn2_name= self.res.vn2_name
#        vn2_subnets= self.res.vn2_subnets
#        policy1_name= 'policy1'
#        policy2_name= 'policy2'
#        rules= [
#            {
#               'direction'     : '<>', 'simple_action' : 'pass',
#               'protocol'      : '1',
#               'source_network': vn1_name,
#               'dest_network'  : vn2_name,
#             },
#                ]
#        rev_rules= [
#            {
#               'direction'     : '<>', 'simple_action' : 'pass',
#               'protocol'      : '1',
#               'source_network': vn2_name,
#               'dest_network'  : vn1_name,
#             },
#                ]
#        policy1_fixture= self.useFixture( PolicyFixture( policy_name= policy1_name, rules_list= rules, inputs= self.inputs,
#                                    connections= self.connections ))
#        policy2_fixture= self.useFixture( PolicyFixture( policy_name= policy2_name, rules_list= rev_rules, inputs= self.inputs,
#                                    connections= self.connections ))
#        vn1_fixture= self.res.vn1_fixture
#        vn1_fixture.bind_policies([policy1_fixture.policy_fq_name], vn1_fixture.vn_id)
#        self.addCleanup( vn1_fixture.unbind_policies, vn1_fixture.vn_id, [policy1_fixture.policy_fq_name] )
#
#        assert vn1_fixture.verify_on_setup()
#        vn2_fixture= self.res.vn2_fixture
#        vn2_fixture.bind_policies([policy2_fixture.policy_fq_name], vn2_fixture.vn_id)
#        self.addCleanup( vn2_fixture.unbind_policies, vn2_fixture.vn_id, [policy2_fixture.policy_fq_name] )        
#        assert vn2_fixture.verify_on_setup()
#
#        vm1_fixture= self.res.vn1_vm1_fixture
#        assert vm1_fixture.verify_on_setup()
#        vm2_fixture= self.res.vn2_vm1_fixture
#        assert vm2_fixture.verify_on_setup()
#        self.nova_fixture.wait_till_vm_is_up( vm1_fixture.vm_obj )
#        self.nova_fixture.wait_till_vm_is_up( vm2_fixture.vm_obj )
#        assert vm1_fixture.ping_to_ip( vm2_fixture.vm_ip )
#        vm_node_ip= vm1_fixture.inputs.host_data[vm1_fixture.nova_fixture.get_nova_host_of_vm(vm1_fixture.vm_obj)]['host_ip']
#        vm_host=vm1_fixture.inputs.host_data[vm_node_ip]['name']
#        self.flow_record=self.analytics_obj.get_flows_vrouter_uve(vrouter=vm_host)
#        assert ( self.flow_record > 0)
#        time.sleep(221)
#        self.flow_record=self.analytics_obj.get_flows_vrouter_uve(vrouter=vm_host)
#        assert ( self.flow_record == 0)
#        assert self.analytics_obj.verify_connected_networks_in_vn_uve(vn1_name,vn2_name)
#        assert self.analytics_obj.verify_connected_networks_in_vn_uve(vn2_name,vn1_name)
#        #assert vm1_fixture.ping_to_ip( vm2_fixture.vm_ip )
#        return True
#    
#

    @preposttest_wrapper
    def test_verify_flow_tables(self):
        ''' Test to validate flow tables

        '''
        vn1_name= self.res.vn1_name
        vn1_fq_name = '%s:%s:%s'%(self.inputs.project_fq_name[0],self.inputs.project_fq_name[1],self.res.vn1_name)
        vn1_subnets= self.res.vn1_subnets
        vn2_name= self.res.vn2_name
        vn2_fq_name = '%s:%s:%s'%(self.inputs.project_fq_name[0],self.inputs.project_fq_name[1],self.res.vn2_name)
        vn2_subnets= self.res.vn2_subnets
        policy1_name= 'policy1'
        policy2_name= 'policy2'
        result = True
        rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'udp',
               'source_network': vn1_name,
               'dest_network'  : vn2_name,
             },
                ]
        rev_rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'udp',
               'source_network': vn2_name,
               'dest_network'  : vn1_name,
             },
                ]
        policy1_fixture= self.useFixture( PolicyFixture( policy_name= policy1_name, rules_list= rules, inputs= self.inputs,
                                    connections= self.connections ))
        policy2_fixture= self.useFixture( PolicyFixture( policy_name= policy2_name, rules_list= rev_rules, inputs= self.inputs,
                                    connections= self.connections ))
        vn1_fixture= self.res.vn1_fixture
        vn1_fixture.bind_policies([policy1_fixture.policy_fq_name], vn1_fixture.vn_id)
        self.addCleanup( vn1_fixture.unbind_policies, vn1_fixture.vn_id, [policy1_fixture.policy_fq_name] )

        assert vn1_fixture.verify_on_setup()
        vn2_fixture= self.res.vn2_fixture
        vn2_fixture.bind_policies([policy2_fixture.policy_fq_name], vn2_fixture.vn_id)
        assert vn2_fixture.verify_on_setup()
        self.addCleanup( vn2_fixture.unbind_policies, vn2_fixture.vn_id, [policy2_fixture.policy_fq_name] )
#        self.res.verify_common_objects()
        #start_time=self.analytics_obj.getstarttime(self.tx_vm_node_ip)
        #installing traffic package in vm
        self.res.vn1_vm1_fixture.install_pkg("Traffic")
        self.res.vn2_vm2_fixture.install_pkg("Traffic")
        self.res.fvn_vm1_fixture.install_pkg("Traffic")

        self.tx_vm_node_ip= self.inputs.host_data[self.nova_fixture.get_nova_host_of_vm(self.res.vn1_vm1_fixture.vm_obj)]['host_ip']
        self.rx_vm_node_ip= self.inputs.host_data[self.nova_fixture.get_nova_host_of_vm(self.res.vn2_vm2_fixture.vm_obj)]['host_ip']
        self.tx_local_host = Host(self.tx_vm_node_ip, self.inputs.username, self.inputs.password)
        self.rx_local_host = Host(self.rx_vm_node_ip, self.inputs.username, self.inputs.password)
        self.send_host = Host(self.res.vn1_vm1_fixture.local_ip)
        self.recv_host = Host(self.res.vn2_vm2_fixture.local_ip)
        pkts_before_traffic = self.analytics_obj.get_inter_vn_stats(self.inputs.collector_ips[0], src_vn=vn1_fq_name, other_vn=vn2_fq_name, direction='in')
        if not pkts_before_traffic:
            pkts_before_traffic = 0
        #import pdb;pdb.set_trace()
        #Create traffic stream
        self.logger.info("Creating streams...")
        stream = Stream(protocol="ip", proto="udp", src=self.res.vn1_vm1_fixture.vm_ip,
                        dst=self.res.vn2_vm2_fixture.vm_ip, dport=9000)

        profile = StandardProfile(stream=stream, size=100,count=10,listener=self.res.vn2_vm2_fixture.vm_ip)
        sender = Sender("sendudp", profile, self.tx_local_host, self.send_host, self.inputs.logger)
        receiver = Receiver("recvudp", profile, self.rx_local_host, self.recv_host, self.inputs.logger)
        start_time=self.analytics_obj.getstarttime(self.tx_vm_node_ip)
        self.logger.info("start time= %s"%(start_time))    
        receiver.start()
        sender.start()
        time.sleep(10)
        #Poll to make usre traffic flows, optional
        #sender.poll()
        #receiver.poll()
        sender.stop()
        receiver.stop()
        print sender.sent, receiver.recv
        assert "sender.sent == receiver.recv", "UDP traffic to ip:%s failed" % self.res.vn2_vm2_fixture.vm_ip
        #Verifying the vrouter uve for the active flow
        vm_node_ip= self.res.vn1_vm1_fixture.inputs.host_data[self.res.vn1_vm1_fixture.nova_fixture.get_nova_host_of_vm(self.res.vn1_vm1_fixture.vm_obj)]['host_ip']
        vm_host=self.res.vn1_vm1_fixture.inputs.host_data[vm_node_ip]['name']
        self.logger.info("Waiting for the %s vrouter uve to be updated with active flows"%(vm_host))
        time.sleep(60)
        self.flow_record=self.analytics_obj.get_flows_vrouter_uve(vrouter=vm_host)
        self.logger.info("Active flow in vrouter uve = %s"%(self.flow_record))
        if ( self.flow_record > 0):
            self.logger.info("Flow records  updated")
            result = result and True
        else:
            self.logger.warn("Flow records NOT updated")
            result = result and False
               
#        assert ( self.flow_record > 0)
#        self.logger.info("Waiting for inter-vn stats to be updated...")
#        time.sleep(60)
        pkts_after_traffic = self.analytics_obj.get_inter_vn_stats(self.inputs.collector_ips[0], src_vn=vn1_fq_name, other_vn=vn2_fq_name, direction='in')
        if not pkts_after_traffic:
            pkts_after_traffic = 0
        self.logger.info("Verifying that the inter-vn stats updated")
        self.logger.info("Inter vn stats before traffic %s"%(pkts_before_traffic))
        self.logger.info("Inter vn stats after traffic %s"%(pkts_after_traffic))
        if ((pkts_after_traffic - pkts_before_traffic) >= 10):
            self.logger.info("Inter vn stats updated")
            result = result and True
        else:
            self.logger.warn("Inter vn stats NOT updated")
            result = result and False

        self.logger.info("Waiting for flow records to be expired...")
        time.sleep(224)
        self.flow_record=self.analytics_obj.get_flows_vrouter_uve(vrouter=vm_host)
#        if ( self.flow_record > 0):
#            self.logger.info("Flow records  updated")
#            result = result and True
#        else:
#            self.logger.warn("Flow records NOT updated")
#            result = result and False
        self.logger.debug("Active flow in vrouter uve = %s"%(self.flow_record))    
#        assert ( self.flow_record == 0)
        #Verifying flow series table
        src_vn='default-domain'+':'+self.inputs.project_name+':'+self.res.vn1_name
        dst_vn='default-domain'+':'+self.inputs.project_name+':'+self.res.vn2_name
        #creating query: '(sourcevn=default-domain:admin:vn1) AND (destvn=default-domain:admin:vn2)'
        query='('+'sourcevn='+src_vn+') AND (destvn='+dst_vn+')'
        for ip in self.inputs.collector_ips: 
            self.logger.info("Verifying flowRecordTable through opserver %s.."%(ip))    
            self.res2=self.analytics_obj.ops_inspect[ip].post_query('FlowRecordTable',start_time=start_time,end_time='now'
                                                 ,select_fields=['sourcevn', 'sourceip', 'destvn', 'destip','setup_time','teardown_time','agg-packets'],
                                                    where_clause=query)

            self.logger.info("Query output: %s"%(self.res2))
            assert self.res2
            if self.res2:  
                r=self.res2[0]
                s_time=r['setup_time']
                e_time=r['teardown_time']
                agg_pkts=r['agg-packets']
                assert (agg_pkts == sender.sent)
            self.logger.info( 'setup_time= %s,teardown_time= %s'%(s_time,e_time))
            self.logger.info("Records=\n%s"%(self.res2))
            #Quering flow sreies table
            self.logger.info("Verifying flowSeriesTable through opserver %s"%(ip))    
            self.res1=self.analytics_obj.ops_inspect[ip].post_query('FlowSeriesTable',start_time=str(s_time),end_time=str(e_time)
                                               ,select_fields=['sourcevn', 'sourceip', 'destvn', 'destip','sum(packets)'],
                                                where_clause=query)
            self.logger.info("Query output: %s"%(self.res1))
            assert self.res1
            if self.res1:  
                r1=self.res1[0]
                sum_pkts=r1['sum(packets)']
                assert (sum_pkts == sender.sent)
            self.logger.info("Flow series Records=\n%s"%(self.res1))
            assert (sum_pkts==agg_pkts)
        
        assert result 
        return True   

#    @preposttest_wrapper
#    def test_active_xmpp_peer_in_vrouter_uve(self):
#        ''' Test vrouter uve for active xmpp connection
#
#        '''
#        assert self.analytics_obj.verify_active_xmpp_peer_in_vrouter_uve()
#        return True

    @preposttest_wrapper
    def test_bgprouter_uve_for_xmpp_and_bgp_peer_count(self):
        ''' Test bgp-router uve for active xmp/bgpp connections count

        '''
        assert self.analytics_obj.verify_bgp_router_uve_xmpp_and_bgp_count()
        return True
    
    @preposttest_wrapper
    def test_verify_hrefs(self):
        ''' Test all hrefs for collector/agents/bgp-routers etc

        '''
        assert self.analytics_obj.verify_hrefs_to_all_uves_of_a_given_uve_type()
        return True
    
    @preposttest_wrapper
    def test_verify__bgp_router_uve_up_xmpp_and_bgp_count(self):
        ''' Test bgp-router uve for up bgp peer/xmpp peer count

        '''
        assert self.analytics_obj.verify_bgp_router_uve_up_xmpp_and_bgp_count()
        return True
    
    @preposttest_wrapper
    def test_verify_connected_networks_based_on_policy(self):
        ''' Test to validate attached policy in the virtual-networks

        '''
        vn1_name= self.res.vn1_name
        vn1_subnets= self.res.vn1_subnets
        vn2_name= self.res.vn2_name
        vn2_subnets= self.res.vn2_subnets
        policy1_name= 'policy1'
        policy2_name= 'policy2'
        rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'icmp',
               'source_network': vn1_name,
               'dest_network'  : vn2_name,
             },
                ]
        rev_rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'icmp',
               'source_network': vn2_name,
               'dest_network'  : vn1_name,
             },
                ]
        policy1_fixture= self.useFixture( PolicyFixture( policy_name= policy1_name, rules_list= rules, inputs= self.inputs,
                                    connections= self.connections ))
        policy2_fixture= self.useFixture( PolicyFixture( policy_name= policy2_name, rules_list= rev_rules, inputs= self.inputs,
                                    connections= self.connections ))
        vn1_fixture= self.res.vn1_fixture
        vn1_fixture.bind_policies([policy1_fixture.policy_fq_name], vn1_fixture.vn_id)
        self.addCleanup( vn1_fixture.unbind_policies, vn1_fixture.vn_id, [policy1_fixture.policy_fq_name] )

        assert vn1_fixture.verify_on_setup()
        vn2_fixture= self.res.vn2_fixture
        vn2_fixture.bind_policies([policy2_fixture.policy_fq_name], vn2_fixture.vn_id)
        assert vn2_fixture.verify_on_setup()
        self.addCleanup( vn2_fixture.unbind_policies, vn2_fixture.vn_id, [policy2_fixture.policy_fq_name] )
#        self.res.verify_common_objects()
        self.logger.info("Verifying the connected_networks based on policy in the vn uve..")
        vn1_fq_name=self.res.vn1_fixture.vn_fq_name
        vn2_fq_name=self.res.vn2_fixture.vn_fq_name
        assert self.analytics_obj.verify_connected_networks_in_vn_uve(vn1_fq_name,vn2_fq_name)
        assert self.analytics_obj.verify_connected_networks_in_vn_uve(vn2_fq_name,vn1_fq_name)
        return True
        
    @preposttest_wrapper
    def test_verify_flow_series_table(self):
        ''' Test to validate flow series table

        '''
        vn1_name= self.res.vn1_name
        vn1_subnets= self.res.vn1_subnets
        vn2_name= self.res.vn2_name
        vn2_subnets= self.res.vn2_subnets
        policy1_name= 'policy1'
        policy2_name= 'policy2'
        rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'udp',
               'source_network': vn1_name,
               'dest_network'  : vn2_name,
             },
                ]
        rev_rules= [
            {
               'direction'     : '<>', 'simple_action' : 'pass',
               'protocol'      : 'udp',
               'source_network': vn2_name,
               'dest_network'  : vn1_name,
             },
                ]
        policy1_fixture= self.useFixture( PolicyFixture( policy_name= policy1_name, rules_list= rules, inputs= self.inputs,
                                    connections= self.connections ))
        policy2_fixture= self.useFixture( PolicyFixture( policy_name= policy2_name, rules_list= rev_rules, inputs= self.inputs,
                                    connections= self.connections ))
        vn1_fixture= self.res.vn1_fixture
        vn1_fixture.bind_policies([policy1_fixture.policy_fq_name], vn1_fixture.vn_id)
        self.addCleanup( vn1_fixture.unbind_policies, vn1_fixture.vn_id, [policy1_fixture.policy_fq_name] )

        assert vn1_fixture.verify_on_setup()
        vn2_fixture= self.res.vn2_fixture
        vn2_fixture.bind_policies([policy2_fixture.policy_fq_name], vn2_fixture.vn_id)
        assert vn2_fixture.verify_on_setup()
        self.addCleanup( vn2_fixture.unbind_policies, vn2_fixture.vn_id, [policy2_fixture.policy_fq_name] )
#        self.res.verify_common_objects()
        #installing traffic package in vm
        self.res.vn1_vm1_fixture.install_pkg("Traffic")
        self.res.vn2_vm2_fixture.install_pkg("Traffic")
        self.res.fvn_vm1_fixture.install_pkg("Traffic")

        self.tx_vm_node_ip= self.inputs.host_data[self.nova_fixture.get_nova_host_of_vm(self.res.vn1_vm1_fixture.vm_obj)]['host_ip']
        self.rx_vm_node_ip= self.inputs.host_data[self.nova_fixture.get_nova_host_of_vm(self.res.vn2_vm2_fixture.vm_obj)]['host_ip']
        self.tx_local_host = Host(self.tx_vm_node_ip, self.inputs.username, self.inputs.password)
        self.rx_local_host = Host(self.rx_vm_node_ip, self.inputs.username, self.inputs.password)
        self.send_host = Host(self.res.vn1_vm1_fixture.local_ip)
        self.recv_host = Host(self.res.vn2_vm2_fixture.local_ip)
        #import pdb;pdb.set_trace()
        #Create traffic stream
        start_time=self.analytics_obj.getstarttime(self.tx_vm_node_ip)
        self.logger.info("start time= %s"%(start_time))    
        for i in range(10):
            count=100
            dport=9000
            count=count * (i+1)
            dport=dport+i
            print 'count=%s'%(count)
            print 'dport=%s'%(dport)

            self.logger.info("Creating streams...")
            stream = Stream(protocol="ip", proto="udp", src=self.res.vn1_vm1_fixture.vm_ip,
                        dst=self.res.vn2_vm2_fixture.vm_ip, dport=dport)

            profile = StandardProfile(stream=stream, size=100,count=count,listener=self.res.vn2_vm2_fixture.vm_ip)
            sender = Sender("sendudp", profile, self.tx_local_host, self.send_host, self.inputs.logger)
            receiver = Receiver("recvudp", profile, self.rx_local_host, self.recv_host, self.inputs.logger)
            receiver.start()
            sender.start()
            sender.stop()
            receiver.stop()
            print sender.sent, receiver.recv
            time.sleep(1)
        vm_node_ip= self.res.vn1_vm1_fixture.inputs.host_data[self.res.vn1_vm1_fixture.nova_fixture.get_nova_host_of_vm(self.res.vn1_vm1_fixture.vm_obj)]['host_ip']
        vm_host=self.res.vn1_vm1_fixture.inputs.host_data[vm_node_ip]['name']
        time.sleep(300)
        #Verifying flow series table
        src_vn='default-domain'+':'+self.inputs.project_name+':'+self.res.vn1_name
        dst_vn='default-domain'+':'+self.inputs.project_name+':'+self.res.vn2_name
        #creating query: '(sourcevn=default-domain:admin:vn1) AND (destvn=default-domain:admin:vn2)'
        query='('+'sourcevn='+src_vn+') AND (destvn='+dst_vn+')'
        for ip in self.inputs.collector_ips: 
            self.logger.info( 'setup_time= %s'%(start_time))
            #Quering flow sreies table
            self.logger.info("Verifying flowSeriesTable through opserver %s"%(ip))    
            self.res1=self.analytics_obj.ops_inspect[ip].post_query('FlowSeriesTable',start_time=start_time,end_time='now'
                                               ,select_fields=['sourcevn', 'sourceip', 'destvn', 'destip','sum(packets)','sport','dport','T=1'],
                                                where_clause=query,sort=2,limit=5,sort_fields=['sum(packets)'])
            assert self.res1
            self.logger.info("Top 5 flows %s"%(self.res1))
        return True   
        
    @preposttest_wrapper
    def test_verify_analytics_process_restarts(self):
        ''' Test to validate process restarts

        '''
        if (len(self.inputs.collector_ips) < 2):
            self.logger.info("collector ips less than 2...skipping the test...")
            return True
        start_time=self.analytics_obj.getstarttime(self.inputs.cfgm_ip)
        vn_name='vn221'
        vn_subnets=['222.1.1.0/24']
        vm1_name='vm_test1'
        start_time=self.analytics_obj.getstarttime(self.inputs.cfgm_ip)
        vn_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,
                     vn_name=vn_name, inputs= self.inputs, subnets= vn_subnets))
        vn_obj= vn_fixture.obj
        vm1_fixture= self.useFixture(VMFixture(connections= self.connections,
                vn_obj=vn_obj, vm_name= vm1_name, project_name= self.inputs.project_name))
        #getting vm uuid
        assert vm1_fixture.verify_on_setup()
        vm_uuid=vm1_fixture.vm_id
        self.logger.info("Waiting for logs to be updated in the database...")
        time.sleep(30)
        query='('+'ObjectId=default-domain:admin:'+vn_name+')'
#        self.logger.info("Verifying ObjectVNTable through opserver %s.."%(self.inputs.collector_ips[0]))
#        self.res2=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectVNTable',
#                                                                                start_time=start_time,end_time='now'
#                                                                                ,select_fields=['ObjectId', 'Source',
#                                                                                'ObjectLog', 'SystemLog','Messagetype',
#                                                                                'ModuleId','MessageTS'],
#                                                                                 where_clause=query)
#        self.logger.info("query output : %s"%(self.res2))
#        assert self.res2 
        result=True
        tmp1=[]
        for ip in self.inputs.collector_ips:
            tmp1.append(ip)
        for ip in tmp1:
            name = socket.gethostbyaddr(ip)
            name= name[0].split('.')[0]
            tmp=tmp1[:]
            tmp.remove(ip)
            #analytics_process_lists=['contrail-opserver','contrail-collector','contrail-qe','redis-uve','contrail-database']
            analytics_process_lists=['contrail-opserver','contrail-collector','contrail-qe','redis-uve']
            self.logger.info("Verifying ObjectVNTable through opserver %s.."%(tmp[0]))
            self.res2=self.analytics_obj.ops_inspect[tmp[0]].post_query('ObjectVNTable',
                                                                    start_time=start_time,end_time='now'
                                                                   ,select_fields=['ObjectId', 'Source',
                                                                    'ObjectLog', 'SystemLog','Messagetype',
                                                                     'ModuleId','MessageTS'],
                                                                      where_clause=query)
            self.logger.info("query output : %s"%(self.res2))
            assert self.res2 
            for process in analytics_process_lists:
                try:
                    self.inputs.stop_service(process,[ip])
                    #self.inputs.restart_service(process,self.inputs.collector_ips[0])
                    self.logger.info("Waiting...")
                    time.sleep(10)
                    self.logger.info("START: verification with %s stopped"%(process))
                    if (not self.analytics_obj.verify_collector_uve_module_state(tmp[0],name,process) or 
                                self.analytics_obj.get_analytics_process_parameters(tmp[0],name,
                                process_parameters='process_state',process= process) == 'PROCESS_STATE_STOPPED' ):

                        self.logger.info("Process state for %s correctly reflected for process %s"%(name,process))
                        result=result and True
                    else:
                        self.logger.error("Process state for %s NOT correctly reflected for process %s"%(name,process))
                        result=result and False

                        
                    if (process == 'contrail-opserver' or process == 'redis-uve' or process == 'contrail-qe' or process == 'contrail-collector'): 
                        for name in self.inputs.compute_names:
                            status=self.analytics_obj.get_connection_status(tmp[0],name,'VRouterAgent')
                            if (status == 'Established'):
                                self.logger.info("Connection is extablished with %s for %s:VRouterAgent"%(tmp[0],name))
                                result=result and True
                            else:
                                self.logger.warn("Connection is not extablished with %s for %s:VRouterAgent"%(tmp[0],name))
                                result= result and False
                            if (process == 'contrail-collector'):
                                self.logger.info("Verifying that the generators connected to other collector...")
                                primary_col=self.analytics_obj.get_primary_collector(opserver=tmp[0],generator=name,moduleid='VRouterAgent')
                                primary_col_ip=primary_col.split(':')[0]
                                if (primary_col_ip == tmp[0]):
                                    self.logger.info("Primary collector properly set to %s"%(primary_col_ip))
                                    result=result and True
                                else:
                                    self.logger.warn("Primary collector properly NOT set to %s"%(tmp[0]))
                                    result=result and False
                                
                        for name in self.inputs.bgp_names:
                            status=self.analytics_obj.get_connection_status(tmp[0],name,'ControlNode')
                            if (status == 'Established'):
                                self.logger.info("Connection is extablished with %s for %s:ControlNode"%(tmp[0],name))
                                result=result and True
                            else:
                                self.logger.warn("Connection is not extablished with %s for %s:ControlNode"%(tmp[0],name))
                                result= result and False
                            if (process == 'contrail-collector'):
                                self.logger.info("Verifying that the generators connected to other collector...")
                                primary_col=self.analytics_obj.get_primary_collector(opserver=tmp[0],generator=name,moduleid='ControlNode')
                                primary_col_ip=primary_col.split(':')[0]
                                if (primary_col_ip == tmp[0]):
                                    self.logger.info("Primary collector properly set to %s"%(primary_col_ip))
                                    result=result and True
                                else:
                                    self.logger.warn("Primary collector properly NOT set to %s"%(tmp[0]))
                                    result=result and False
                    if (process == 'contrail-database'):
                        self.logger.info("Verifying ObjectVNTable through opserver %s.."%(tmp[0]))
                        self.res2=self.analytics_obj.ops_inspect[tmp[0]].post_query('ObjectVNTable',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
                        self.logger.info("query output : %s"%(self.res2))
                        assert self.res2 
                
            
                except Exception as e:
                    print e
                    result=result and False
                finally:
                    self.logger.info("END : verification with %s stopped"%(process))
                    self.inputs.start_service(process,[ip])
                    time.sleep(20)
                    if self.analytics_obj.verify_collector_uve_module_state(tmp[0],name,process):
                        self.logger.info("Process state for %s correctly reflected for process %s"%(name,process))
                        result=result and True
                    else:
                        self.logger.error("Process state for %s NOT correctly reflected for process %s"%(name,process))
                        result=result and False
                          
        assert result
        return True
    

    @preposttest_wrapper
    def test_verify_opserver_connection_on_process_restarts_controlnode(self):
        ''' Test to validate process restarts

        '''
        control_node_process=['contrail-control']
        result=True
        state=self.analytics_obj.get_peer_state_info(self.inputs.collector_ips[0],(self.inputs.bgp_names[0],self.inputs.bgp_names[1]))
        self.logger.info("state %s"%(state))
        if (state['last_state']== 'OpenConfirm' and state['state']== 'Established'):
            self.logger.info("peer state correctly shown in the bgp-peer uve")
            result=result and True
        else:
            result=result and False
            assert result
        initial_falp_count=self.analytics_obj.get_peer_falp_info(self.inputs.collector_ips[0],(self.inputs.bgp_names[1],self.inputs.bgp_names[0]))

        if initial_falp_count:
            initial_falp_count=initial_falp_count['flap_count']
        else:
            self.logger.info("flap count not sent")
            initial_falp_count=0
        
        #Verifying the xmpp peering with the compute nodes before the process restarts
        for name in self.inputs.bgp_names:
            for ip in self.inputs.compute_ips:
                peer=(name,ip)
                connection_state=self.analytics_obj.get_xmpp_peer_state_info(self.inputs.collector_ips[0],peer)
                if connection_state:
                    if (connection_state['state'] == 'Established'):
                        result=result and True
                        self.logger.info("%s:%s xmpp is established"%(name,ip))
                    else:
                        result=result and False
                        self.logger.info("%s:%s xmpp is not established"%(name,ip))
                        
        self.logger.info("initial flap count = %s "%(initial_falp_count))
        for process in control_node_process:
            try:
                self.inputs.stop_service(process,[self.inputs.bgp_ips[0]])
                time.sleep(120)
                status=self.analytics_obj.get_connection_status(self.inputs.collector_ips[0],self.inputs.bgp_names[0],'ControlNode')
                if (status == 'Established'):
                    self.logger.warn("Connection is extablished with %s for %s:ControlNode"%(self.inputs.collector_ips[0],self.inputs.bgp_names[0]))
                    result=result and False 
                if (self.analytics_obj.verify_bgp_peers_in_opserver((self.inputs.bgp_names[0],self.inputs.bgp_names[1]))):
                    self.logger.info("BGP peer uve shown in the opserver list of bgp-peers uve")
                    result=result and True 
                else:
                    result=result and False
                    self.logger.warn("BGP peer uve not shown in the opserver list of bgp-peers uve")
                output=self.analytics_obj.get_bgp_peer_uve(self.inputs.collector_ips[0],(self.inputs.bgp_names[0],self.inputs.bgp_names[1]))
                if not output:
                    result=result and True
                    self.logger.info("BGP peer uve not shown in the opserver")
                else:
                    result=result and False 
                    self.logger.info("BGP peer uve  shown in the opserver %s"%(output))
                
                event_info=self.analytics_obj.get_peer_event_info(self.inputs.collector_ips[0],(self.inputs.bgp_names[1],self.inputs.bgp_names[0]))
                if (event_info['last_event']== 'fsm::EvTcpConnectFail'):
                    self.logger.info("bgp-peer not established")
                    result=result and True
                else:
                    self.logger.warn("bgp-peer still established")
                    result=result and False
                final_falp_count=self.analytics_obj.get_peer_falp_info(self.inputs.collector_ips[0],(self.inputs.bgp_names[1],self.inputs.bgp_names[0]))

                if final_falp_count:
                    self.logger.info("Flap count uve sent")
                    final_falp_count=final_falp_count['flap_count']
                    result=result and True
                else:
                    self.logger.warn("Flap count not sent")
                    result=result and False
                    final_falp_count= 0
    
                self.logger.info("final flap count = %s "%(final_falp_count))
                if (final_falp_count > initial_falp_count):
                    self.logger.info("flap count incrementing")
                    result=result and True
                else:
                    self.logger.info("flap count not incrementing")
                    self.logger.info("flap count after restart %s "%(final_falp_count))
                    result=result and False
                    
                
            except Exception as e:
                print e
            finally:
                self.inputs.start_service(process,[self.inputs.bgp_ips[0]])
                time.sleep(20)
                status=self.analytics_obj.get_connection_status(self.inputs.collector_ips[0],self.inputs.bgp_names[0],'ControlNode')
                if (status == 'Established'):
                    self.logger.info("Connection is established with %s for %s:ControlNode"%(self.inputs.collector_ips[0],self.inputs.bgp_names[0]))
                    result=result and True 
                if self.analytics_obj.verify_bgp_peers_in_opserver((self.inputs.bgp_names[0],self.inputs.bgp_names[1])):
                    time.sleep(10)
                    self.logger.info("BGP peer uve shown in the opserver")
                    result=result and True
                else:
                    self.logger.warn("BGP peer uve not shown in the opserver")
                    result=result and False 

                state=self.analytics_obj.get_peer_state_info(self.inputs.collector_ips[0],(self.inputs.bgp_names[0],self.inputs.bgp_names[1]))
                self.logger.info("state %s"%(state))
                if (state['last_state']== 'OpenConfirm' and state['state']== 'Established'):
                    self.logger.info("peer state correctly shown in the bgp-peer uve")
                    result=result and True
                else:
                    self.logger.warn("Connection is not established with %s for %s:ControlNode"%(self.inputs.collector_ips[0],self.inputs.bgp_names[0]))
                    result= result and False
                for name in self.inputs.bgp_names:
                    for ip in self.inputs.compute_ips:
                        peer=(name,ip)
                        connection_state=self.analytics_obj.get_xmpp_peer_state_info(self.inputs.collector_ips[0],peer)
                        if connection_state:
                            if (connection_state['state'] == 'Established'):
                                result=result and True
                                self.logger.info("%s:%s xmpp is established"%(name,ip))
                            else:
                                result=result and False
                                self.logger.info("%s:%s xmpp is not established"%(name,ip))

        assert result
        return True
    

    @preposttest_wrapper
    def test_verify_opserver_connection_on_process_restarts_compute_node(self):
        ''' Test to validate process restarts compute node

        '''
        compute_node_process=['contrail-vrouter']
        result=True
        for name in self.inputs.bgp_names:
            peer=(name,self.inputs.compute_ips[0])
            connection_state=self.analytics_obj.get_xmpp_peer_state_info(self.inputs.collector_ips[0],peer)
            if connection_state:
                if (connection_state['state'] == 'Established'):
                    result=result and True
                    self.logger.info("%s:%s xmpp is established"%(name,self.inputs.compute_ips[0]))
                else:
                    result=result and False
                    self.logger.info("%s:%s xmpp is not established"%(name,self.inputs.compute_ips[0]))
#            initial_flap_count=self.analytics_obj.get_xmpp_peer_flap_info(self.inputs.collector_ips[0],peer)
#
#            if initial_flap_count:
#                initial_flap_count=initial_flap_count['flap_count']
#            else:
#                self.logger.info("Flap count not sent")
#                initial_flap_count=0
#            self.logger.info("Initial flap coung= %s "%(initial_flap_count))

        for process in compute_node_process:
            try:
                self.inputs.stop_service(process,[self.inputs.compute_ips[0]])
                time.sleep(60)
                status=self.analytics_obj.get_connection_status(self.inputs.collector_ips[0],self.inputs.compute_names[0],'VRouterAgent')
                if (status == 'Established'):
                    self.logger.warn("Connection is established with %s for %s:VrouterAgent"%(self.inputs.collector_ips[0],self.inputs.compute_names[0]))
                    result=result and False 
                else:
                    self.logger.info("Connection is not established with %s for %s:VrouterAgent"%(self.inputs.collector_ips[0],self.inputs.compute_names[0]))
                    result= result and True
                for name in self.inputs.bgp_names:
                    peer=(name,self.inputs.compute_ips[0])
                    connection_state=self.analytics_obj.get_xmpp_peer_state_info(self.inputs.collector_ips[0],peer)
                    if connection_state:
                        if (connection_state['state'] == 'Established'):
                            result=result and False 
                            self.logger.warn("%s:%s xmpp is established"%(name,self.inputs.compute_ips[0]))
                        else:
                            result=result and True
                            self.logger.info("%s:%s xmpp is not established"%(name,self.inputs.compute_ips[0]))
#                    final_flap_count=self.analytics_obj.get_xmpp_peer_flap_info(self.inputs.collector_ips[0],peer)
#
#                    if final_flap_count:
#                        self.logger.info("Flap count sent")
#                        result=result and True
#                        final_flap_count=final_flap_count['flap_count']
#                    else:
#                        self.logger.warn("Flap count not sent")
#                        final_flap_count=0
#                        result=result and False
#                
#                    if (final_flap_count > initial_flap_count):
#                        result=result and True
#                        self.logger.info("Flap count is incrementing")
#                    else:
#                        result=result and False
#                        self.logger.warn("Flap count is not incrementing")
#
#                    event=self.analytics_obj.get_xmpp_peer_event_info(self.inputs.collector_ips[0],peer)
#                    if event:
#                        last_event=event['last_event']
#                        if (last_event == 'xmsm::EvTcpClose'):
#                            result=result and True
#                            self.logger.info("Last event logged properly as xmsm::EvTcpClose")
#                        else:
#                            result=result and False
#                            self.logger.warn("Last event NOT logged properly as xmsm::EvTcpClose")
#                    else:
#                        result=result and False
#                        self.logger.warn("Last event not logged")
#                        

            except Exception as e:
                print e
            finally:
                self.inputs.start_service(process,[self.inputs.compute_ips[0]])
                time.sleep(60)
                status=self.analytics_obj.get_connection_status(self.inputs.collector_ips[0],self.inputs.compute_names[0],'VRouterAgent')
                if (status == 'Established'):
                    self.logger.info("Connection is established with %s for %s:VrouterAgent"%(self.inputs.collector_ips[0],self.inputs.compute_names[0]))
                    result=result and True 
                else:
                    self.logger.warn("Connection is not established with %s for %s:VrouterAgent"%(self.inputs.collector_ips[0],self.inputs.compute_names[0]))
                    result= result and False
                for name in self.inputs.bgp_names:
                    peer=(name,self.inputs.compute_ips[0])
                    connection_state=self.analytics_obj.get_xmpp_peer_state_info(self.inputs.collector_ips[0],peer)
                    if connection_state:
                        if (connection_state['state'] == 'Established'):
                            result=result and True 
                            self.logger.info("%s:%s xmpp is established"%(name,self.inputs.compute_ips[0]))
                        else:
                            result=result and False
                            self.logger.warn("%s:%s xmpp is not established"%(name,self.inputs.compute_ips[0]))
                    else:
                        result=result and False
                        self.logger.warn("Connection states not logged")

        assert result
        return True
    

    @preposttest_wrapper
    def test_verify_bgp_peer_uve(self):
        ''' Test to validate bgp peer uve

        '''
        #assert self.analytics_obj.verify_bgp_peers_in_opserver((self.inputs.bgp_ips[0],self.inputs.bgp_ips[1]))
        abc= self.analytics_obj.get_peer_stats_info_tx_proto_stats(self.inputs.collector_ips[0],(self.inputs.bgp_names[0],self.inputs.bgp_names[1]))
        assert abc
        return True
    

    @preposttest_wrapper
    def test_verify_object_logs(self):
        ''' Test to validate object logs 

        '''
        vn_name='vn22'
        vn_subnets=['22.1.1.0/24']
        vm1_name='vm_test'
        start_time=self.analytics_obj.getstarttime(self.inputs.cfgm_ip)
        vn_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,
                     vn_name=vn_name, inputs= self.inputs, subnets= vn_subnets))
        vn_obj= vn_fixture.obj
        vm1_fixture= self.useFixture(VMFixture(connections= self.connections,
                vn_obj=vn_obj, vm_name= vm1_name, project_name= self.inputs.project_name))
        #getting vm uuid
        assert vm1_fixture.verify_on_setup()
        vm_uuid=vm1_fixture.vm_id
        self.logger.info("Waiting for logs to be updated in the database...")
        time.sleep(10)
        #creating query: '(ObjectId=default-domain:admin:vn1)'
        query='('+'ObjectId=default-domain:admin:'+vn_name+')'
        result=True
        self.logger.info("Verifying ObjectVNTable through opserver %s.."%(self.inputs.collector_ips[0]))    
        self.res2=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectVNTable',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
        self.logger.info("query output : %s"%(self.res2))
        if not self.res2:
            st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
            self.logger.info("status: %s"%(st))
        assert self.res2
        
        self.logger.info("Getting object logs for vm")
        query='('+'ObjectId='+ vm_uuid +')'
        self.logger.info("Verifying ObjectVMTable through opserver %s.."%(self.inputs.collector_ips[0]))    
        self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectVMTable',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
        self.logger.info("query output : %s"%(self.res1))
        if not self.res1:
            st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
            self.logger.info("status: %s"%(st))
        assert self.res1
        
        self.logger.info("Getting object logs for ObjectRoutingInstance table")
#        object_id=self.inputs.project_fq_name[0]+':'+self.inputs.project_fq_name[1]+vn_name+':'+vn_name
        object_id='%s:%s:%s:%s'%(self.inputs.project_fq_name[0],self.inputs.project_fq_name[1],vn_name,vn_name)
#        query='('+'ObjectId=default-domain:admin:'+vn_name+')'
        query='(ObjectId=%s)'%(object_id)
        
        self.logger.info("Verifying ObjectRoutingInstance through opserver %s.."%(self.inputs.collector_ips[0]))    
        self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectRoutingInstance',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
        self.logger.info("query output : %s"%(self.res1))
        if not self.res1:
            self.logger.warn("ObjectRoutingInstance  query did not return any output")
            st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
            self.logger.info("status: %s"%(st))
        assert self.res1
        return True
    

    @preposttest_wrapper
    def test_verify_bgp_peer_object_logs(self):
        ''' Test to validate bgp_peer_object logs 

        '''
        if (len(self.inputs.bgp_ips) < 2):
            self.logger.info("bgp ips less than 2...skipping the test...")
            return True
        result = True
        try:
            start_time=self.analytics_obj.getstarttime(self.inputs.bgp_ips[0])
            start_time1=self.analytics_obj.getstarttime(self.inputs.compute_ips[0])
            object_id= 'default-domain:default-project:ip-fabric:__default__:'+self.inputs.bgp_names[1]+':default-domain:default-project:ip-fabric:__default__:'+self.inputs.bgp_names[0]
            object_id1=self.inputs.bgp_ips[0]
            query='('+'ObjectId='+ object_id +')'
            query1='('+'ObjectId='+ object_id1 + ' AND Source='+self.inputs.compute_names[0]+' AND ModuleId=VRouterAgent)'
#            query1='('+'ObjectId='+ object_id1 +')' 
            self.logger.info("Stopping the control node in %s"%(self.inputs.bgp_ips[0]))
            self.inputs.stop_service('contrail-control',[self.inputs.bgp_ips[0]])
            self.logger.info("Waiting for the logs to be updated in database..")
            time.sleep(20)
            self.logger.info("Verifying ObjectBgpPeer Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectBgpPeer',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)

            self.logger.info("Verifying ObjectXmppConnection Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res2=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectXmppConnection',
                                                                                start_time=start_time1,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query1)
#            self.logger.info("query output : %s"%(self.res1))
            if not self.res1:
                self.logger.info("query output : %s"%(self.res1))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
            if not self.res2:
                self.logger.info("query output : %s"%(self.res2))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
            if self.res1:
                self.logger.info("Verifying logs from ObjectBgpPeer table")
                result1=False
                result2=False
                for elem in self.res1:
                    if re.search('EvConnectTimerExpired',str(elem['ObjectLog'])):
                        self.logger.info("EvConnectTimerExpired log sent")
                        result1 = True
                    if re.search('EvTcpConnectFail',str(elem['ObjectLog'])):
                        self.logger.info("EvTcpConnectFail log sent")
                        result2 = True
                if not result1:
                        self.logger.warn("EvConnectTimerExpired log NOT sent")
                if not result2:
                        self.logger.warn("EvTcpConnectFail log NOT sent")
                    
            if self.res2:
                self.logger.info("Verifying logs from ObjectXmppConnection table")
                result6=False
                for elem in self.res2:
                    if re.search('EvTcpConnectFail',str(elem['ObjectLog'])):
                        self.logger.info("EvTcpConnectFail log sent")
                        result6 = True
                if not result6:
                        self.logger.warn("EvTcpConnectFail log NOT sent")
                        
            start_time=self.analytics_obj.getstarttime(self.inputs.bgp_ips[0])
            start_time1=self.analytics_obj.getstarttime(self.inputs.compute_ips[0])
            time.sleep(2)
            self.inputs.start_service('contrail-control',[self.inputs.bgp_ips[0]])
            self.logger.info("Waiting for the logs to be updated in database..")
            time.sleep(30)
            self.logger.info("Verifying ObjectBgpPeer Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectBgpPeer',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
            
            self.logger.info("Verifying ObjectXmppConnection Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res2=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectXmppConnection',
                                                                                start_time=start_time1,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query1)
#            self.logger.info("query output : %s"%(self.res1))
            if not self.res1:
                self.logger.info("query output : %s"%(self.res1))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
            if not self.res2:
                self.logger.info("query output : %s"%(self.res2))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
            if self.res1:
                self.logger.info("Verifying logs from ObjectBgpPeer table")
                result3=False
                result4=False
                result5=False
                for elem in self.res1:
                    if re.search('EvTcpPassiveOpen',str(elem['ObjectLog'])):
                        self.logger.info("EvTcpPassiveOpen log sent")
                        result3 = True
                    if re.search('OpenConfirm',str(elem['ObjectLog'])):
                        self.logger.info("OpenConfirm log sent")
                        result4=True
                    if re.search('Established',str(elem['ObjectLog'])):
                        self.logger.info("Established log sent")
                        result5 = True
                if not result3:
                        self.logger.warn("EvTcpPassiveOpen log NOT sent")
                if not result4:
                        self.logger.warn("OpenConfirm log NOT sent")
                if not result5:
                        self.logger.warn("Established log NOT sent")
                    
                     
            if self.res2:
                self.logger.info("Verifying logs from ObjectXmppConnection table")
                result7=False
                result8=False
                for elem in self.res2:
                    if re.search('EvXmppOpen',str(elem['ObjectLog'])):
                        self.logger.info("EvXmppOpen log sent")
                        result7 = True
                    if re.search('EvTcpConnected',str(elem['ObjectLog'])):
                        self.logger.info("EvTcpConnected log sent")
                        result8 = True
                if not result7:
                        self.logger.warn("EvXmppOpen log NOT sent")
                if not result8:
                        self.logger.warn("EvTcpConnected log NOT sent")
        except Exception as e:
            print e
            result=result and False
        finally:
            self.inputs.start_service('contrail-control',[self.inputs.bgp_ips[0]])
            time.sleep(4)
            result = result and result1 and result2 and result3 and result4 and result5 and result6 and result7 and result8
            assert result
            return True
        
    @preposttest_wrapper
    def test_verify_xmpp_peer_object_logs(self):
        ''' Test to validate xmpp peer object logs 
        '''
        result = True
        try:
            start_time=self.analytics_obj.getstarttime(self.inputs.compute_ips[0])
            object_id= self.inputs.bgp_names[0]+':'+self.inputs.compute_ips[0]
            query='('+'ObjectId='+ object_id +')'
            self.logger.info("Stopping the xmpp node in %s"%(self.inputs.compute_ips[0]))
            self.inputs.stop_service('contrail-vrouter',[self.inputs.compute_ips[0]])
            self.logger.info("Waiting for the logs to be updated in database..")
            time.sleep(20)
            self.logger.info("Verifying ObjectXmppPeerInfo Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectXmppPeerInfo',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
#            self.logger.info("query output : %s"%(self.res1))
            if not self.res1:
                self.logger.info("query output : %s"%(self.res1))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
                        
            start_time=self.analytics_obj.getstarttime(self.inputs.compute_ips[0])
            time.sleep(2)
            self.inputs.start_service('contrail-vrouter',[self.inputs.compute_ips[0]])
            self.logger.info("Waiting for the logs to be updated in database..")
            time.sleep(30)
            self.logger.info("Verifying ObjectXmppPeerInfo Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectXmppPeerInfo',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
#            self.logger.info("query output : %s"%(self.res1))
            if not self.res1:
                self.logger.info("query output : %s"%(self.res1))
                st=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].send_trace_to_database (node= self.inputs.collector_names[0], module= 'QueryEngine',trace_buffer_name= 'QeTraceBuf')
                self.logger.info("status: %s"%(st))
                result = result and False
                     
        except Exception as e:
            print e
            result=result and False
        finally:
#            start_time=self.analytics_obj.getstarttime(self.inputs.compute_ips[0])
            self.inputs.start_service('contrail-vrouter',[self.inputs.compute_ips[0]])
            time.sleep(20)
            self.logger.info("Verifying ObjectVRouter Table through opserver %s.."%(self.inputs.collector_ips[0]))    
            object_id= self.inputs.compute_names[0]
            query='('+'ObjectId='+ object_id +')'
            self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectVRouter',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
            if (self.res1):
                self.logger.info("ObjectVRouter table query passed")
                result = result and True
                self.logger.info("Query output: %s"%(self.res1))
            else:
                self.logger.warn("ObjectVRouter table query failed")
                result = result and False
                
                
            assert result
            return True

    @preposttest_wrapper
    def test_object_log_verification_with_delete_add_in_network_mode(self):
        """Verifying the uve and object log for service instance and service template"""

        self.vn1_fq_name = "default-domain:admin:" + self.res.vn1_name
        self.vn1_name=self.res.vn1_name
        self.vn1_subnets= self.res.vn1_subnets
        self.vm1_name= self.res.vn1_vm1_name
        self.vn2_fq_name = "default-domain:admin:" + self.res.vn2_name
        self.vn2_name= self.res.vn2_name
        self.vn2_subnets= self.res.vn2_subnets
        self.vm2_name= self.res.vn2_vm2_name
        self.action_list = []
        self.if_list = [['management', False], ['left', True], ['right', True]]
        self.st_name = 'in_net_svc_template_1'
        si_prefix = 'in_net_svc_instance_'
        si_count = 1
        svc_scaling= False 
        max_inst= 1 
        svc_mode= 'in-network'

        self.policy_name = 'policy_in_network'
        result = True    
        try:
            start_time=self.analytics_obj.getstarttime(self.inputs.cfgm_ip)
            if getattr(self, 'res', None):
                self.vn1_fixture= self.res.vn1_fixture
                self.vn2_fixture= self.res.vn2_fixture
                assert self.vn1_fixture.verify_on_setup()
                assert self.vn2_fixture.verify_on_setup()
            else:
                self.vn1_fixture = self.config_vn(self.vn1_name, self.vn1_subnets)
                self.vn2_fixture = self.config_vn(self.vn2_name, self.vn2_subnets)
            self.st_fixture, self.si_fixtures = self.config_st_si(self.st_name, si_prefix, si_count, svc_scaling, max_inst, left_vn=self.vn1_fq_name, right_vn=self.vn2_fq_name, svc_mode= svc_mode)
            self.action_list = self.chain_si(si_count, si_prefix)
            self.rules = [
                        {
                        'direction'     : '<>',
                        'protocol'      : 'any',
                        'source_network': self.vn1_name,
                        'src_ports'     : [0, -1],
                        'dest_network'  : self.vn2_name,
                        'dst_ports'     : [0, -1],
                        'simple_action' : None,
                        'action_list'   : {'apply_service': self.action_list}
                        },
                    ]
            self.policy_fixture = self.config_policy(self.policy_name, self.rules)

            self.vn1_policy_fix = self.attach_policy_to_vn(self.policy_fixture, self.vn1_fixture)
            self.vn2_policy_fix = self.attach_policy_to_vn(self.policy_fixture, self.vn2_fixture)

            if getattr(self, 'res', None):
                self.vm1_fixture= self.res.vn1_vm1_fixture
                self.vm2_fixture= self.res.vn2_vm2_fixture
            else:
                self.vm1_fixture = self.config_vm(self.vn1_fixture, self.vm1_name)
                self.vm2_fixture = self.config_vm(self.vn2_fixture, self.vm2_name)
            assert self.vm1_fixture.verify_on_setup()
            assert self.vm2_fixture.verify_on_setup()
            self.nova_fixture.wait_till_vm_is_up(self.vm1_fixture.vm_obj)
            self.nova_fixture.wait_till_vm_is_up(self.vm2_fixture.vm_obj)

            self.validate_vn(self.vn1_name)
            self.validate_vn(self.vn2_name)
            for si_fix in self.si_fixtures:
                si_fix.verify_on_setup()

        #Ping from left VM to right VM
            errmsg = "Ping to right VM ip %s from left VM failed" % self.vm2_fixture.vm_ip
            assert self.vm1_fixture.ping_with_certainty(self.vm2_fixture.vm_ip), errmsg
            domain,project,name=self.si_fixtures[0].si_fq_name
            si_name='%s:%s:%s'%(domain,project,name)
            assert self.analytics_obj.verify_si_st_uve(instance=si_name,left_vn=self.vn1_fq_name,right_vn= self.vn2_fq_name)
            self.logger.info("Verifying the object logs...")
            obj_id_lst=self.analytics_obj.get_uve_key(uve='service-instances')
            obj_id1_lst=self.analytics_obj.get_uve_key(uve='service-chains')
            for elem in obj_id_lst:
                query='('+'ObjectId='+ elem +')'
                self.logger.info("Verifying ObjectSITable Table through opserver %s.."%(self.inputs.collector_ips[0]))    
                self.res1=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ObjectSITable',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
                if self.res1:
                    self.logger.info("SI object logs received %s"%(self.res1))
                    result = result and True
                else:
                    self.logger.warn("SI object logs NOT received ")
                    result = result and False
                    

            for elem in obj_id1_lst:
                query='('+'ObjectId='+ elem +')'
                self.logger.info("Verifying ServiceChain Table through opserver %s.."%(self.inputs.collector_ips[0]))    
                self.res2=self.analytics_obj.ops_inspect[self.inputs.collector_ips[0]].post_query('ServiceChain',
                                                                                start_time=start_time,end_time='now'
                                                                                ,select_fields=['ObjectId', 'Source',
                                                                                'ObjectLog', 'SystemLog','Messagetype',
                                                                                'ModuleId','MessageTS'],
                                                                                 where_clause=query)
                if self.res2:
                    self.logger.info("ST object logs received %s"%(self.res1))
                    result = result and True
                else:
                    self.logger.warn("ST object logs NOT received ")
                    result = result and False
        except Exception as e:
            self.logger.warn("Got exception as %s"%(e))
        return True
#        return self.svc_obj.verify_policy_delete_add()
#
    @preposttest_wrapper
    def test_colector_uve_module_sates(self):
        '''Test to validate collector uve.
        '''
        result=True
        process_list = ['redis-query', 'contrail-qe','contrail-collector','contrail-analytics-nodemgr','redis-uve','contrail-opserver','redis-sentinel']
        for process in process_list:
            result = result and self.analytics_obj.verify_collector_uve_module_state(self.inputs.collector_names[0],self.inputs.collector_names[0],process)
        assert result
        return True
    
    @preposttest_wrapper
    def test_config_node_uve_states(self):
        '''Test to validate config node uve.
        '''
        result=True
        process_list = ['contrail-discovery', 'redis-config','contrail-config-nodemgr','contrail-svc-monitor','ifmap','contrail-api','contrail-schema']
        for process in process_list:
            result = result and self.analytics_obj.verify_cfgm_uve_module_state(self.inputs.collector_names[0],self.inputs.cfgm_names[0],process)
        assert result
        return True
#end AnalyticsTestSanity

