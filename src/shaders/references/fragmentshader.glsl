uniform vec4 sunDir;
				
// tex0=heightmap, tex1=dirt, tex2=grass, tex3=rock, tex4=snow
uniform sampler2D tex0, tex1, tex2, tex3, tex4;
				
// .x = min height, .y = max height, .z = min slope, .w = max slope
uniform vec4 snowData;
uniform vec4 rockData;
uniform vec4 dirtData;
uniform vec4 grassData;
				
// .x=grass, .y=dirt, .z=rock, .w=snow
uniform vec4 mapStrength;
				
varying float height;
varying vec3 triTexCoords;
								
vec3 light = -normalize( sunDir.xyz );

// this comes from the book Real-Time 3D Terrain Engines Using C++ And DirectX 
float computeWeight(float value, float minExtent, float maxExtent)
{
	float weight = 0.0;
				
	if(value >= minExtent && value <= maxExtent)
	{
		float range = maxExtent - minExtent;
		
		weight = value - minExtent;
						
		// convert to [0, 1] based on its distance to midpoint of the extents
		weight *= 1.0 / range;
		weight -= 0.5;
		weight *= 2.0;
						
		// square result for non-linear falloff
		weight *= weight;
						
		// invert and bound check
		weight = 1.0 - abs(weight);
		weight = clamp(weight, 0.001, 1.0);
	}
					
	return weight;
}
				
void main( void )
{
	vec4 texel = texture2D(tex0, triTexCoords.xz) * 2.0 - 1.0;
	// Use max because of numerical issues
	float ny = sqrt(max(1.0 - texel.b*texel.b - texel.a*texel.a, 0.0));		
	vec3 normal = vec3(texel.b, ny, texel.a);

	// Wrap lighting for sun
	float l = max( dot( normal, light ), 0.0 ) * 0.5 + 0.5;
					
	// slope: 1.0 = steep, 0.0 = flat
	float slope = 1.0 - ny;
					
	vec4 weights = vec4(0.0, 0.0, 0.0, 0.0);
	
	// once all 3 lookups have been done for a texture these weights
	// say how much of the sum of those lookups to use
	weights.x = computeWeight(height, rockData.x, rockData.y) * 
				computeWeight(slope, rockData.z, rockData.w) * mapStrength.z;
	weights.y = computeWeight(height, dirtData.x, dirtData.y) * 
				computeWeight(slope, dirtData.z, dirtData.w) * mapStrength.y;
	weights.z = computeWeight(height, snowData.x, snowData.y) * 
				computeWeight(slope, snowData.z, snowData.w) * mapStrength.w;
	weights.w = computeWeight(height, grassData.x, grassData.y) * 
				computeWeight(slope, grassData.z, grassData.w) * mapStrength.x;
	weights *= 1.0 / (weights.x + weights.y + weights.z + weights.w);
					
	// this comes from the gpu gems 3 article: 
	// generating complex procedural terrains using the gpu
	// used to determine how much of each planar lookup to use
	// for each texture
	vec3 tpweights = abs(normal);
	tpweights = (tpweights - 0.2) * 7.0;
	tpweights = max(tpweights, vec3(0.0, 0.0, 0.0));
	tpweights /= (tpweights.x + tpweights.y + tpweights.z).xxx;
				
	vec4 finalColor = vec4(0.0, 0.0, 0.0, 1.0);
	vec4 tempColor = vec4(0.0, 0.0, 0.0, 1.0);
						
	// dirt
	tempColor = tpweights.z * texture2D(tex1, triTexCoords.xy*5.0);
	tempColor += tpweights.x * texture2D(tex1, triTexCoords.yz*5.0);
	tempColor += tpweights.y * texture2D(tex1, triTexCoords.xz*5.0);
	finalColor += weights.y * tempColor;

	// grass
	tempColor = tpweights.z * texture2D(tex2, triTexCoords.xy*5.0);
	tempColor += tpweights.x * texture2D(tex2, triTexCoords.yz*5.0);
	tempColor += tpweights.y * texture2D(tex2, triTexCoords.xz*5.0);
	finalColor += weights.w * tempColor;
	
	// rock
	tempColor = tpweights.z * texture2D(tex3, triTexCoords.xy*5.0);
	tempColor += tpweights.x * texture2D(tex3, triTexCoords.yz*5.0);
	tempColor += tpweights.y * texture2D(tex3, triTexCoords.xz*5.0);
	finalColor += weights.x * tempColor;
	
	// snow
	tempColor = tpweights.z * texture2D(tex4, triTexCoords.xy*5.0);
	tempColor += tpweights.x * texture2D(tex4, triTexCoords.yz*5.0);
	tempColor += tpweights.y * texture2D(tex4, triTexCoords.xz*5.0);
	finalColor += weights.z * tempColor;
					
	gl_FragColor = finalColor * l;
}