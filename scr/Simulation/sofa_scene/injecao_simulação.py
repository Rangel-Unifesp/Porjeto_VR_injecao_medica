try:
    import Sofa
    import Sofa.Core
except ImportError:
    print("ERRO: As bibliotecas do SOFA não foram encontradas.")


def create_injection_scene(parent_node: Sofa.Core.Node):
    print("Injecao.py: Configurando a cena da simulação de injeção...")

    # --- Configurações Gerais da Cena ---
    parent_node.gravity = [0.0, -9810.0, 0.0]
    parent_node.dt = 0.02  # Timestep da simulação

    # --- Plugins Necessários ---
    parent_node.addObject('RequiredPlugin', pluginName=[
        'Sofa.Component.IO.Mesh',
        'Sofa.Component.LinearSolver.Direct',
        'Sofa.Component.Mass',
        'Sofa.Component.ODESolver.Backward',
        'Sofa.Component.SolidMechanics.FEM.Elastic',
        'Sofa.Component.Topology.Container.Dynamic',
        'Sofa.Component.Collision.Detection.Algorithm',
        'Sofa.Component.Collision.Detection.Intersection',
        'Sofa.Component.Collision.Response.Contact',
        'Sofa.Component.Constraint.Projective',
        'Sofa.GUI.Component' # Para visualizar (opcional, mas bom para debug)
    ])
    
    # --- Pipeline de Colisão ---
    parent_node.addObject('DefaultPipeline', name='CollisionPipeline')
    parent_node.addObject('BruteForceBroadPhase')
    parent_node.addObject('BVHNarrowPhase')
    parent_node.addObject('DefaultContactManager', name='Response', response='FrictionContactConstraint')

    # --- 1. O Tecido (Objeto Deformável) ---
    tissue = parent_node.addChild('Tissue')
    tissue.addObject('EulerImplicitSolver', name='OdeSolver')
    tissue.addObject('SparseLDLSolver', name='LinearSolver')
    tissue.addObject('MeshVTKLoader', name='VtkLoader', filename='mesh/liver.vtk') # Use uma malha sua
    tissue.addObject('TetrahedronSetTopologyContainer', name='Topology', src='@VtkLoader')
    tissue.addObject('MechanicalObject', name='Mechanical', template='Vec3d')
    tissue.addObject('TetrahedronFEMForceField', template='Vec3d', name='FEM', youngModulus=500, poissonRatio=0.45)
    tissue.addObject('UniformMass', totalMass=0.5)
    tissue.addObject('FixedConstraint', indices='0 1 2 3 4 5 6 7') # Fixa a base do tecido

    # Modelo de colisão para o tecido
    tissue_collision = tissue.addChild('Collision')
    tissue_collision.addObject('TriangleSetTopologyContainer', name='StiffyTriangle')
    tissue_collision.addObject('TriangleSetTopologyModifier')
    tissue_collision.addObject('TriangleCollisionModel', moving=True, simulated=True)
    tissue_collision.addObject('LineCollisionModel', moving=True, simulated=True)
    tissue_collision.addObject('PointCollisionModel', moving=True, simulated=True)
    needle = parent_node.addChild('Needle')
    needle_mo = needle.addObject('MechanicalObject', name='Instrument',
                                 position=[0, 50, 0,   
                                           0, 30, 0],  
                                 showObject=True, showObjectScale=5.0, drawMode=2) 


    needle_collision = needle.addChild('Collision')

    needle_collision.addObject('PointCollisionModel', name='NeedleTip', moving=True, simulated=False, indices='1')
    
    interaction_force = needle.addObject('Restitution', name='InteractionForce',
                                         contactManager='@../Response',
                                         collidingModel='@Collision/NeedleTip',
                                         restitutionModel='FrictionContactConstraint')

    print("Injecao.py: Cena configurada com sucesso.")


    return {"needle_mo": needle_mo, "interaction_force": interaction_force }