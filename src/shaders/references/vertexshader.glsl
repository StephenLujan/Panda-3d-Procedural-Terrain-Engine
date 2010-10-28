uniform vec4 terBlockParams;
attribute float terHeight;
varying float height;
varying vec3 triTexCoords;
				
void main( void )
{
	vec4 newPos = vec4(gl_Vertex.x * terBlockParams.z + terBlockParams.x, terHeight,
						gl_Vertex.z * terBlockParams.z + terBlockParams.y, gl_Vertex.w);

	//vec4 pos = calcWorldPos(newPos);
	pos = newPos;
	triTexCoords = newPos.xyz;
	height = pos.y;

	gl_Position = gl_ModelViewProjectionMatrix * pos;
}