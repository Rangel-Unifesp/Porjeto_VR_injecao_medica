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
    # Carrega o modelo 3D do corpo. O caminho é relativo à pasta onde a simulação é iniciada.
    tissue.addObject('MeshOBJLoader', name='BodyLoader', filename='models/male_body.glb')
    tissue.addObject('TetrahedronSetTopologyContainer', name='Topology', src='@BodyLoader')
    tissue.addObject('MechanicalObject', name='Mechanical', template='Vec3d')
    tissue.addObject('TetrahedronFEMForceField', template='Vec3d', name='FEM', youngModulus=1000, poissonRatio=0.45)
    tissue.addObject('UniformMass', totalMass=1.0) # Ajuste a massa conforme necessário
    # Fixa alguns pontos do modelo para que ele não caia.
    # Os índices aqui são um palpite e precisam ser ajustados para o seu modelo.
    tissue.addObject('FixedConstraint', indices='10 21 35 45 55 65')

    # Modelo de colisão para o tecido
    tissue_collision = tissue.addChild('Collision')
    tissue_collision.addObject('TriangleSetTopologyModifier')
    tissue_collision.addObject('TriangleCollisionModel', name="TissueCollisionModel", moving=True, simulated=True)
    tissue_collision.addObject('LineCollisionModel', name="TissueLineCollisionModel", moving=True, simulated=True)
    tissue_collision.addObject('PointCollisionModel', name="TissuePointCollisionModel", moving=True, simulated=True)
    
    # --- 2. A Agulha (Objeto Rígido Controlado) ---
    needle = parent_node.addChild('Needle')
    needle_mo = needle.addObject('MechanicalObject', name='Instrument',
                                 position=[0, 50, 0,  # Ponto final da agulha (cabo)
                                           0, 30, 0], # Ponto inicial da agulha (ponta)
                                 showObject=True, showObjectScale=2.0, drawMode=2) # drawMode=2 para desenhar como linha

    # Modelo de colisão para a ponta da agulha
    needle_collision = needle.addChild('Collision')
    # Usamos apenas o índice 1 (a ponta) para a detecção de colisão
    needle_collision.addObject('PointCollisionModel', name='NeedleTip', moving=True, simulated=False, tags='NeedleTipTag')
    
    # --- 3. Força de Interação ---
    # Esta força é calculada quando a ponta da agulha colide com o tecido.
    interaction_force = needle.addObject('Restitution', name='InteractionForce',
                                         contactManager='@../Response',
                                         collidingModel='@Collision/NeedleTip',
                                         restitutionModel='FrictionContactConstraint',
                                         listening=True) # Habilita a escuta das forças

    print("Injecao.py: Cena configurada com sucesso.")

    return {"needle_mo": needle_mo, "interaction_force": interaction_force}