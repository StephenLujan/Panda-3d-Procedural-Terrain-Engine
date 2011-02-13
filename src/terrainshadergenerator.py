###
# Author: Stephen Lujan
###
# This file contains a shader generator specific to the terrain
###

_beginning = '''
//Cg
//Cg profile arbvp1 arbfp1

struct vfconn
{
    float2 l_texcoord0 : TEXCOORD0;
    float2 l_texcoord3 : TEXCOORD3;
    float4 l_position  : POSITION;
    float2 l_slope_brightness: TEXCOORD2;
    float3 l_mpos;//      : FOG;
    //float3 l_normal;
};

vfconn vshader( in float4 vtx_position : POSITION,
	      in float3 vtx_normal : NORMAL,
              in float2 vtx_texcoord0 : TEXCOORD0,
              in float2 vtx_texcoord3 : TEXCOORD3,
              in uniform float4x4 mat_modelproj,
	      in uniform float4x4 trans_model_to_world,
	      in uniform float4 k_lightvec,
	      in uniform float4 k_lightcolor,
	      in uniform float4 k_ambientlight,
	      in uniform float4 k_tscale
          //out vfconn OUT
            )
{
    vfconn OUT;

    OUT.l_position=mul(mat_modelproj,vtx_position);
    OUT.l_texcoord0=vtx_texcoord0*k_tscale;
    OUT.l_texcoord3=vtx_texcoord3;

    // worldspace position, for clipping in the fragment shader
    OUT.l_mpos = mul(trans_model_to_world, vtx_position);

    // lighting
    //WTF IS THIS NECESSARY
    vtx_normal.x *= -400;
    vtx_normal.y *= -400;
    //k_lightvec.z /= 400;
    float3 N = normalize( vtx_normal );
    float3 L = normalize( k_lightvec.xyz );

    float3 UP = float3(0,0,1);
    OUT.l_slope_brightness.x = 1.0 - dot( N, UP );

    OUT.l_slope_brightness.y = (max( dot( -N, L ), 0.0f )*k_lightcolor)+k_ambientlight;
    //OUT.l_normal = N;
    return OUT;
}

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

void fshader(   in  vfconn IN,
                in uniform float4 k_waterlevel      : WATERLEVEL,
                out float4 o_color                  : COLOR,
                in uniform sampler2D detailTexture  : DETAILTEXTURE,
'''

_middle = '''            )
{
    // clipping
    //if ( IN.l_mpos.z < k_waterlevel.z) discard;

    //unpack some input
    // 0 = horizontal 1 = vertical
    float slope = IN.l_slope_brightness.x; //0.45;
    float brightness = IN.l_slope_brightness.y;
    float height = IN.l_mpos.z;

    //set up texture calculations
    float textureWeight = 0.0;
    float textureWeightTotal = 0.000001;
    vec4 terrainColor = float4(0.0, 0.0, 0.0, 1.0);

'''

_end = '''
    // normalize color
    terrainColor /= textureWeightTotal;
    // detail texture
    float2 detailTexCoord= IN.l_texcoord0*8.0;
    terrainColor*= tex2D(detailTexture, detailTexCoord);
    // alpha splatting and lighting
    o_color=terrainColor*(brightness);
    //HDRL
    o_color = (o_color*o_color + o_color) / (o_color*o_color + o_color + float4(1.0, 1.0, 1.0, 1.0));
    o_color.a=1.0;
}'''


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
        terrainColor += textureWeight * tex2D(texUnit''' + texStr + ''', IN.l_texcoord0);
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


    def createShader(self, name='stephen5.sha'):

        self.feedThePanda()
        string = _beginning + self.getParameters() + _middle + self.getCode() + _end
        f = open('./shaders/' + name, 'w')
        f.write(string)
