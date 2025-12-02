import { Canvas } from '@react-three/fiber'
import { OrbitControls, Text } from '@react-three/drei'
import { useMemo } from 'react'
import './SkillVisualization.css'

function SkillSphere({ skills }) {
  const skillObjects = useMemo(() => {
    if (!skills || skills.length === 0) return []

    const radius = 3
    const objects = []

    skills.forEach((skill, index) => {
      const angle = (index / skills.length) * Math.PI * 2
      const x = Math.cos(angle) * radius
      const z = Math.sin(angle) * radius
      const y = (Math.random() - 0.5) * 2

      const levelColors = {
        // High-contrast colors against the purple gradient background
        beginner: '#4FC3F7',      // light blue
        intermediate: '#FFD54F',  // warm yellow
        advanced: '#FF7043'       // vivid orange
      }

      objects.push({
        position: [x, y, z],
        color: levelColors[skill.level] || '#666',
        name: skill.name,
        level: skill.level
      })
    })

    return objects
  }, [skills])

  return (
    <>
      {skillObjects.map((obj, index) => (
        <group key={index} position={obj.position}>
          <mesh>
            <sphereGeometry args={[0.4, 16, 16]} />
            <meshStandardMaterial color={obj.color} emissive={obj.color} emissiveIntensity={0.5} />
          </mesh>
          <Text
            position={[0, 0.8, 0]}
            fontSize={0.15}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
          >
            {obj.name}
          </Text>
        </group>
      ))}
    </>
  )
}

function SkillVisualization({ skills }) {
  if (!skills || skills.length === 0) {
    return (
      <div className="visualization-container">
        <div className="visualization-placeholder">
          <p>Upload a resume to see skill visualization</p>
        </div>
      </div>
    )
  }

  return (
    <div className="visualization-container">
      <h3>3D Skill Visualization</h3>
      <div className="canvas-wrapper">
        <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <pointLight position={[-10, -10, -10]} />
          <SkillSphere skills={skills} />
          <OrbitControls enableZoom={true} enablePan={true} enableRotate={true} />
        </Canvas>
      </div>
      <div className="legend">
        <div className="legend-item">
          <span className="legend-color beginner"></span>
          <span>Beginner</span>
        </div>
        <div className="legend-item">
          <span className="legend-color intermediate"></span>
          <span>Intermediate</span>
        </div>
        <div className="legend-item">
          <span className="legend-color advanced"></span>
          <span>Advanced</span>
        </div>
      </div>
    </div>
  )
}

export default SkillVisualization

