###
# Author: Stephen Lujan
###
# This file contains a shader generator specific to the terrain
###

_beginning = '''
//Cg
// Should use per-pixel lighting, hdr1, and medium bloom
// input alight0, dlight0

float calculateWeight( float value, float max, float min )
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

struct vfconn
{
    //from terrain shader
    float3 l_tex_coord : TEXCOORD0;
    float3 l_normal : COLOR1;
    float3 l_worldpos : TEXCOORD1;

    //from auto shader
    float4 l_eye_position : TEXCOORD3;
    float4 l_eye_normal : TEXCOORD4;
    //vshader output should not go to fshader, separated
    //float4 l_position : POSITION;
};

void vshader(
        in float4 vtx_texcoord0 : TEXCOORD0,
        in float4 vtx_position : POSITION,
        in float4 vtx_normal : NORMAL,

        out vfconn output,
        out float4 l_position : POSITION,

        uniform float4x4 trans_model_to_world,
        uniform float4x4 mat_modelproj,
        uniform float4x4 trans_model_to_view,
        uniform float4x4 tpose_view_to_model
) {
        l_position = mul(mat_modelproj, vtx_position);
        output.l_eye_position = mul(trans_model_to_view, vtx_position);
        output.l_eye_normal.xyz = mul(tpose_view_to_model, vtx_normal);// vtx_texcoord0.xyz);
        output.l_eye_normal.w = 0;

        //for terrain
        output.l_tex_coord = vtx_texcoord0;
        //output.l_normal =  mul(trans_model_to_world, vtx_normal); //vec3(1.0,0.0,1.0);
        output.l_normal = vtx_normal.xyz;
        output.l_normal.z /= 400;
        output.l_normal = normalize(output.l_normal);
        output.l_worldpos = mul(trans_model_to_world, vtx_position);
}

void fshader(
        //in float4 l_eye_position : TEXCOORD0,
        //in float4 l_eye_normal : TEXCOORD1,
        in vfconn input,
        uniform float4 alight_alight0,
        uniform float4x4 dlight_dlight0_rel_view,
        out float4 o_color : COLOR0,
        uniform float4 attr_color,
        uniform float4 attr_colorscale,

        //from terrain shader
        in uniform sampler2D detailTexture  : DETAILTEXTURE,
'''

_middle = '''
) {
        //set up texture calculations
        float4 result;
        // Fetch all textures.
        float slope = 1.0 - dot( input.l_normal, vec3(0,0,1));
        float height = input.l_worldpos.z;
        float textureWeight = 0.0;
        float textureWeightTotal = 0.000001;
        vec4 terrainColor = float4(0.0, 0.0, 0.0, 1.0);

'''


_end = '''
        // normalize color
        terrainColor /= textureWeightTotal;
        // detail texture
        float2 detailTexCoord= input.l_tex_coord*8.0;
        terrainColor*= tex2D(detailTexture, detailTexCoord) *1.15;
        attr_color = terrainColor;

        // Correct the surface normal for interpolation effects
        input.l_eye_normal.xyz = normalize(input.l_eye_normal.xyz);
        // Begin view-space light calculations
        float ldist,lattenv,langle;
        float4 lcolor,lspec,lvec,lpoint,latten,ldir,leye,lhalf;	 float4 tot_ambient = float4(0,0,0,0);
        float4 tot_diffuse = float4(0,0,0,0);
        // Ambient Light 0
        lcolor = alight_alight0;
        tot_ambient += lcolor;
        // Directional Light 0
        lcolor = dlight_dlight0_rel_view[0];
        lspec  = dlight_dlight0_rel_view[1];
        lvec   = dlight_dlight0_rel_view[2];
        lcolor *= saturate(dot(input.l_eye_normal.xyz, lvec.xyz));
        tot_diffuse += lcolor;
        // Begin view-space light summation
        result = float4(0,0,0,0);
        result += tot_ambient * attr_color;
        result += tot_diffuse * attr_color;
        // End view-space light calculations
        result *= attr_colorscale;
        result.a = 0.5;
        result.rgb = (result*result*result + result*result + result) / (result*result*result + result*result + result + 1);
        o_color = result * 1.000001;
}
'''


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

    def getParameters(self):

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

    def getCode(self):

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
        string = ''
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
        self.feedThePanda()
        return _beginning + self.getParameters() + _middle + self.getCode() + _end

    def saveShader(self, name='shaders/stephen6.sha'):
        string = self.createShader()
        f = open( name , 'w')
        f.write(string)
