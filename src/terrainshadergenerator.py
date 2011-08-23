###
# Author: Stephen Lujan
###
# This file contains a shader generator specific to the terrain
###


class TerrainShaderTexture:

    def __init__(self, tex):

        self.tex = tex
        self.regions = []

    def addRegion(self, region):

        self.regions.append(region)



class TerrainShaderGenerator:

    def __init__(self, terrain):

        self.terrain = terrain
        self.textures = []
        self.normalMapping = True
        self.glare = False

    def bulkCode(self):

        self._header = '''
//Cg
// Should use per-pixel lighting, hdr1, and medium bloom
// input alight0, dlight0

'''
        self._header += 'const float slopeScale = '
        self._header += str(self.terrain.maxHeight / self.terrain.horizontalScale) + ';'
        self._header += '\nconst float normalStrength = 2.0;'
        self._beginning = '''

float3 absoluteValue(float3 input)
{
    return float3(abs(input.x), abs(input.y), abs(input.z));
    float3 output = input;
    if (output.x <= 0)
        output.x = -output.x;
    if (output.y <= 0)
        output.y = -output.y;
    return output;
}

float calculateWeight( float value, float min, float max )
{
    if (value > max)
        return 0.0;
    if (value < min)
        return 0.0;

    //return 1.0;

    float weight = 0.0;

    weight = value - min < max - value ?
             value - min : max - value;

    //weight /= max - min;
    //weight *= weight;
    //weight = log2( weight );
    //weight = sqrt( weight );

    weight+= 0.001;
    //weight = clamp(weight, 0.001, 1.0);
    return weight;
}

float calculateFinalWeight( float height, float slope, float4 limits )
{
    return calculateWeight(height, limits.x, limits.y)
           * calculateWeight(slope, limits.z, limits.a);
}

float3 reflectVector( float3 input, float3 normal)
{
    return ( -2 * dot(input,normal) * normal + input );
}

struct vfconn
{
    //from terrain shader
    float2 l_tex_coord : TEXCOORD0;
    float3 l_normal : TEXCOORD1;
    float3 l_world_pos : TEXCOORD2;

    //from auto shader
    float4 l_eye_position : TEXCOORD3;
    float4 l_eye_normal : TEXCOORD4;
    //vshader output should not go to fshader, separated
    //float4 l_position : POSITION;
};

void vshader(
        in float2 vtx_texcoord0 : TEXCOORD0,
        in float4 vtx_position : POSITION,
        in float4 vtx_normal : NORMAL,

        out vfconn output,
        out float4 l_position : POSITION,

        uniform float4x4 trans_model_to_world,
        uniform float4x4 mat_modelproj,
        uniform float4x4 trans_model_to_view,
        uniform float4x4 tpose_view_to_model,
        //test
        //uniform float4x4 tpose_model_to_world,
        uniform float4x4 itp_modelview,
        uniform float4x4 itp_projection,
        uniform float4x4 itp_modelproj
) {
        // Transform the current vertex from object space to clip space
        l_position = mul(mat_modelproj, vtx_position);

        //for terrain
        output.l_tex_coord = vtx_texcoord0;
        output.l_world_pos = mul(trans_model_to_world, vtx_position);
        output.l_normal = vtx_normal.xyz;
        //output.l_normal.z *= zScale;
        output.l_normal.x *= slopeScale;
        output.l_normal.y *= slopeScale;
        output.l_normal = normalize(output.l_normal);
        //vtx_normal.xyz = output.l_normal;

        output.l_eye_position = mul(trans_model_to_view, vtx_position);
        output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
        output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
}

void fshader(
        in vfconn input,
        uniform float4 alight_alight0,
        //uniform float4x4 dlight_dlight0_rel_view,
        uniform float4x4 dlight_dlight0_rel_world,
        out float4 o_color : COLOR0,
        uniform float4 attr_color,
        uniform float4 attr_colorscale,

        //from terrain shader
        in uniform sampler2D normalMap  : NORMALMAP,
        in uniform sampler2D detailTex  : DETAILTEX,
'''

        self._middle = '''
) {
        //set up texture calculations
        // Fetch all textures.
        float slope = 1.0 - dot( input.l_normal, vec3(0,0,1));
        float height = input.l_world_pos.z;
        float textureWeight = 0.0;
        float textureWeightTotal = 0.000001;
        vec4 terrainColor = float4(0.0, 0.0, 0.0, 1.0);

'''


        self._end = '''
        // normalize color
        terrainColor /= textureWeightTotal;
        attr_color = terrainColor;
        //attr_color =  float4(1.0,1.0,1.0,1.0); //lighting test

        // detail texture
        float2 detailCoordSmall = input.l_tex_coord * 17.0;
        float2 detailCoordBig = input.l_tex_coord * 5.0;
        float2 detailCoordHuge = input.l_tex_coord * 1.6;
        attr_color *= 1.5 * (tex2D(detailTex, detailCoordSmall) * tex2D(detailTex, detailCoordBig) * tex2D(detailTex, detailCoordHuge));
'''
        if self.normalMapping:
            self._end += '''
        // normal mapping
        float3 normalModifier = (tex2D(normalMap, detailCoordSmall) * 4.0 + tex2D(normalMap, detailCoordBig) * 4.0 + tex2D(normalMap, detailCoordHuge) * 4.0) - 6.0;
        input.l_normal *= normalModifier.z/normalStrength;
        input.l_normal.x += normalModifier.x;
        input.l_normal.y += normalModifier.y;
        input.l_normal = normalize(input.l_normal);
'''

        self._end += '''
        // Begin view-space light calculations
        float ldist,lattenv,langle;
        float4 lcolor,lspec,lvec,lpoint,latten,ldir,leye,lhalf;
        float4 tot_ambient = float4(0,0,0,0);
        float4 tot_diffuse = float4(0,0,0,0);
        // Ambient Light 0
        lcolor = alight_alight0;
        tot_ambient += lcolor;
        // Directional Light 0
        lcolor = dlight_dlight0_rel_world[0];
        lspec  = dlight_dlight0_rel_world[1];
        lvec   = dlight_dlight0_rel_world[2];
        //lvec.xyz = normalize(lvec.xyz);
        float dlight_angle = saturate(dot(input.l_normal.xyz, lvec.xyz));
        dlight_angle *= sqrt(dlight_angle);
'''
        if self.glare:
            self._end += '''
        //glare direct sun... should glare on reflection over normal instead.
        dlight_angle -= 0.002 * dlight_angle / (dlight_angle-1.005);
'''
        self._end += '''
        lcolor *= dlight_angle;

        tot_diffuse += lcolor;
        // Begin view-space light summation
        float4 result = float4(0,0,0,0.5);
        result += tot_ambient * attr_color;
        result += tot_diffuse * attr_color;
        result *= attr_colorscale;
        // End view-space light calculations

        // Debug view slopes
        //result.rgb = slope * float3(1.0,1.0,1.0) * 2.0;
        // Debug view surface normals
        //result.rgb = absoluteValue(input.l_normal) * 1.3;
        // Debug view eye normals
        //result.rgb = input.l_eye_normal.xyz * 2.0;
        // Debug view Light only
        //result = tot_diffuse + tot_ambient;
        // Debug view DLight only
        // result = tot_diffuse;

        //hdr0   brightness drop 1 -> 3/4
        //result.rgb = (result*result*result + result*result + result) / (result*result*result + result*result + result + 1);
        //hdr1   brightness drop 1 -> 2/3
        result.rgb = (result*result + result) / (result*result + result + 1.0);
        //hdr2   brightness drop 1 -> 1/2
        //result.rgb = (result) / (result + 1);

        o_color = result * 1.000001;
}
'''

    def addTexture(self, texture):

        self.textures.append(TerrainShaderTexture(texture))

    def addRegionToTex(self, region, textureNumber=-1):

        #bail out if there are no textures to avoid crash
        if len(self.textures) < 1:
            return
        #default to the last texture
        if textureNumber == -1:
            textureNumber = len(self.textures) - 1

        self.textures[textureNumber].addRegion(region)

    def getfShaderParameters(self):

        texNum = 0
        regionNum = 0
        string = ''
        for tex in self.textures:
            string += '''
            in uniform sampler2D texUnit''' + str(texNum) + ' : TEXUNIT' + str(texNum) + ','
            texNum += 1
            for region in tex.regions:
                string += '''
                in uniform float4 region''' + str(regionNum) + 'Limits : REGION' + str(regionNum) + 'LIMITS,'
                regionNum += 1
        return string[:-1] #trim last comma

    def getTextureCode(self):

        texNum = 0
        regionNum = 0
        string = ''
        for tex in self.textures:
            for region in tex.regions:
                texStr = str(texNum)
                regionStr = str(regionNum)
                string += '''

    //texture''' + texStr + ', region ' + regionStr + '''
    textureWeight = calculateFinalWeight(height, slope, region''' + regionStr + '''Limits);
    if (textureWeight)
    {
        textureWeightTotal += textureWeight;
        terrainColor += textureWeight * tex2D(texUnit''' + texStr + ''', input.l_tex_coord);
    }
'''
                regionNum += 1
            texNum += 1
        return string

    def feedThePanda(self):

        texNum = 0
        regionNum = 0
        for tex in self.textures:
            self.terrain.setShaderInput('texUnit' + str(texNum), tex.tex)
            for region in tex.regions:
                key = 'region' + str(regionNum) + 'Limits'
                value = region
                #self.terrain.shaderRegions[key] = value
                self.terrain.setShaderInput(key, value)
                regionNum += 1
            texNum += 1

    def createShader(self):
        self.bulkCode()
        self.feedThePanda()
        return self._header + self._beginning + self.getfShaderParameters() + self._middle + self.getTextureCode() + self._end

    def saveShader(self, name='shaders/stephen6.sha'):
        string = self.createShader()
        f = open(name, 'w')
        f.write(string)
