###
# Author: Stephen Lujan
###
# This file contains a shader generator specific to the terrain
###

from terraintexturemap import *
from pandac.PandaModules import PTAFloat
from panda3d.core import Shader

###############################################################################
#   TerrainShaderGenerator
###############################################################################

class TerrainShaderGenerator:

    def __init__(self, terrain, textureMapper = None):

        self.terrain = terrain
        if not textureMapper:
            textureMapper = TextureMapper(terrain)
        self.textureMapper = textureMapper
        self.normalMapping = True
        self.glare = False
        self.avoidConditionals = 1
        self.fogExponential()
        print "setting basic terrain shader input..."

        self.setShaderFloatInput("fogDensity", self.fogDensity)
        self.setShaderFloatInput("normalMapStrength", 2.5)
        self.setShaderFloatInput("detailSmallScale", 1.3)
        self.setShaderFloatInput("detailBigScale", 7.0)
        self.setShaderFloatInput("detailHugeScale", 23.0)
        print "done"

    def setShaderFloatInput(self, name, input):
        self.terrain.setShaderInput(name, PTAFloat([input]))

    def addTexture(self, texture):
        self.textureMapper.addTexture(texture)

    def addRegionToTex(self, region, textureNumber=-1):

        self.textureMapper.addRegionToTex(region, textureNumber)

    def fogLinear(self):
        # We need to figure out what fog density we want.
        # Lets find out what density results in 80% fog at max view distance

        self.fogDensity = 0.8 * (self.terrain.maxViewRange)
        self.fogFunction = '''
float FogAmount( float maxDistance, float3 PositionVS )
{
    float z = length( PositionVS ); // viewer position is at origin
    return saturate( 1-(z / maxDistance));
}'''
        
    def fogExponential(self):
        # We need to figure out what fog density we want.
        # Lets find out what density results in 75% fog at max view distance
        # the basic fog equation...
        # fog = e^ (-density * z)
        # -density * z = ln(fog) / ln(e)
        # -density * z = ln(fog)
        # density = ln(fog) / -z
        # density = ln(0.25) / -maxViewRange
        self.fogDensity = 1.38629436 / (self.terrain.maxViewRange)
        self.fogFunction = '''
float FogAmount( float density, float3 PositionVS )
{
    float z = length( PositionVS ); // viewer position is at origin
    return saturate( pow(2.7182818, -(density * z)));
}'''

    def fogExponential2(self):
        # We need to figure out what fog density we want.
        # Lets find out what density results in 80% fog at max view distance
        # the basic fog equation...
        #
        # fog = e^ (-density * z)*(-density * z)
        # -density^2 * z^2 = ln(fog) / ln(e)
        # -density^2 * z^2 = ln(fog)
        # density = root(ln(fog) / -z^2)
        # density = root(ln(0.2) / -maxViewRange * maxViewRange)

        self.fogDensity = 1.60943791 / (self.terrain.maxViewRange * self.terrain.maxViewRange)
        self.fogFunction = '''
float FogAmount( float density, float3 PositionVS )
{
    float z = length( PositionVS ); // viewer position is at origin
    float exp = density * z;
    return saturate( pow(2.7182818, -(exp * exp)));
}'''

    def createShader(self):
        self.feedThePanda()
        
        shader = self.getHeader()
        shader += self.getFunctions()
        shader += self.getVertexFragmentConnector()
        shader += self.getVertexShader()
        shader += self.getFragmentShaderTop()
        shader += self.getFShaderTerrainParameters()
        shader += self.getTerrainPrepCode()
        shader += self.getTerrainTextureCode()
        shader += self.getFragmentShaderEnd()
        return shader

    def saveShader(self, name='shaders/stephen6.sha'):
        string = self.createShader()
        f = open(name, 'w')
        f.write(string)

###############################################################################
#   BakedTerrainShaderGenerator
###############################################################################

class BakedTerrainShaderGenerator(TerrainShaderGenerator):

    def getHeader(self):

        header = '''
//Cg
// Should use per-pixel lighting, hdr1, and medium bloom
// input alight0, dlight0

'''
        header += 'const float slopeScale = '
        header += str(self.terrain.maxHeight / self.terrain.horizontalScale) + ';'
        return header
    
    def getFunctions(self):
        functions = ''
        if self.fogDensity:
            functions += '''
//returns [0,1] fog factor
'''
            functions += self.fogFunction
        functions += '''

float3 absoluteValue(float3 input)
{
    return float3(abs(input.x), abs(input.y), abs(input.z));
}

float3 reflectVector( float3 input, float3 normal)
{
    return ( -2 * dot(input,normal) * normal + input );
}
'''
        return functions
    
    
    def getVertexFragmentConnector(self):
        vfconn ='''
struct vfconn
{
    //from terrain shader
    float2 l_tex_coord : TEXCOORD0;
    float3 l_normal : TEXCOORD1;
    float3 l_world_pos : TEXCOORD2;

    //from auto shader
    float4 l_eye_position : TEXCOORD4;
    float4 l_eye_normal : TEXCOORD5;
'''
        if self.fogDensity:
            vfconn +='''
    float l_fog : FOG;'''

        vfconn +='''
};
'''
        return vfconn
    
    def getVertexShader(self):
        vShader ='''
void vshader(
        in float2 vtx_texcoord0 : TEXCOORD0,
        in float4 vtx_position : POSITION,
        in float4 vtx_normal : NORMAL,

        out vfconn output,
        out float4 l_position : POSITION,

        uniform float fogDensity: FOGDENSITY,
        uniform float3 camPos : CAMPOS,
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
'''
        if self.fogDensity:
            vShader +='''
        // there has to be a faster way to get the camera's coordinates in a shader
        float3 cam_to_vertex = output.l_world_pos - camPos;
        output.l_fog = FogAmount(fogDensity, cam_to_vertex);

'''

        vShader +='''
        output.l_normal = vtx_normal.xyz;
        output.l_normal.x *= slopeScale;
        output.l_normal.y *= slopeScale;
        output.l_normal = normalize(output.l_normal);
        //vtx_normal.xyz = output.l_normal;

        //output.l_eye_position = mul(trans_model_to_view, vtx_position);
        //output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
        //output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
}
'''
        return vShader
    
    def getFragmentShaderTop(self):
        fshader ='''
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
        in uniform float normalMapStrength : NORMALMAPSTRENGTH,
        in uniform float detailSmallScale,
        in uniform float detailBigScale,
        in uniform float detailHugeScale,
        '''
        if self.fogDensity:
            fshader += '''
        in uniform float4 fogColor : FOGCOLOR,
'''
        return fshader

    def getFShaderTerrainParameters(self):

        texNum = 0
        string = ''
        #base textures
        for tex in self.textureMapper.textures:
            string += '''
            in uniform sampler2D texUnit''' + str(texNum) + ' : TEXUNIT' + str(texNum) + ','
            texNum += 1
        #alpha maps
        for tex in self.textureMapper.textures:
            string += '''
            in uniform sampler2D texUnit''' + str(texNum) + ' : TEXUNIT' + str(texNum) + ','
            texNum += 1
        return string[:-1] #trim last comma

    def getTerrainPrepCode(self):
        fshader = '''
) {
'''
#        if self.fogDensity:
        if False:
            fshader += '''
        if (input.l_fog == 1.0)
        {
            o_color = fogColor;
            return;
        }
'''
        fshader += '''
        //set up texture calculations
        // Fetch all textures.
        float slope = 1.0 - dot( input.l_normal, vec3(0,0,1));
        vec4 terrainColor = float4(0.0, 0.0, 0.0, 1.0);

'''
        return fshader
    

    def getTerrainTextureCode(self):

        texNum = 0
        string = ''
        for tex in self.textureMapper.textures:
            string += '''
              float4 tex'''+ str(texNum) +' = tex2D(texUnit'+ str(texNum) +', input.l_tex_coord);'
            texNum += 1
            
        totalBaseTextures = texNum
        texNum = 0
        for tex in self.textureMapper.textures:
            string += '''
              float alpha'''+ str(texNum) +' = tex2D(texUnit'+ str(texNum + totalBaseTextures) +', input.l_tex_coord).z;'
            texNum += 1
          
        texNum = 0
        for tex in self.textureMapper.textures:
            string += '''
               terrainColor += tex'''+ str(texNum) +'*alpha'+ str(texNum) +';'
            texNum += 1
        return string
    
    def getFragmentShaderEnd(self):

        fshader = '''
        attr_color = terrainColor;
        //attr_color =  float4(1.0,1.0,1.0,1.0); //lighting test

        // detail texture
        float2 detailCoordSmall = input.l_tex_coord * detailSmallScale;
        float2 detailCoordBig = input.l_tex_coord * detailBigScale;
        float2 detailCoordHuge = input.l_tex_coord * detailHugeScale;
        attr_color *= 1.5 * (tex2D(detailTex, detailCoordSmall) * tex2D(detailTex, detailCoordBig) * tex2D(detailTex, detailCoordHuge));
'''
        if self.normalMapping:
            fshader += '''
        // normal mapping
        float3 normalModifier = tex2D(normalMap, detailCoordSmall) + tex2D(normalMap, detailCoordBig) + tex2D(normalMap, detailCoordHuge) - 1.5;
        input.l_normal *= normalModifier.z/normalMapStrength;
        input.l_normal.x += normalModifier.x;
        input.l_normal.y += normalModifier.y;
        input.l_normal = normalize(input.l_normal);
'''

        fshader += '''
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
            fshader += '''
        //glare direct sun... should glare on reflection over normal instead.
        dlight_angle -= 0.002 * dlight_angle / (dlight_angle-1.005);
'''
        fshader += '''
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
'''
        if self.fogDensity:
            fshader += '''
        result = lerp( fogColor, result, input.l_fog );
'''
        fshader += '''
        o_color = result * 1.000001;
}
'''
        return fshader


    def feedThePanda(self):

        return
            
   
###############################################################################
#   FullTerrainShaderGenerator
###############################################################################           
            
class FullTerrainShaderGenerator(TerrainShaderGenerator):

    def getHeader(self):

        header = '''
//Cg
// Should use per-pixel lighting, hdr1, and medium bloom
// input alight0, dlight0

'''
        header += 'const float slopeScale = '
        header += str(self.terrain.maxHeight / self.terrain.horizontalScale) + ';'
        return header
    
    def getFunctions(self):
        functions = ''
        if self.fogDensity:
            functions += '''
//returns [0,1] fog factor
'''
            functions += self.fogFunction
        functions += '''

float3 absoluteValue(float3 input)
{
    return float3(abs(input.x), abs(input.y), abs(input.z));
}
'''

        if self.avoidConditionals == 0:
            functions += '''
float calculateWeight( float value, float minimum, float maximum )
{
    if (value < minimum)
        return 0.0;
    if (value > maximum)
        return 0.0;

    float weight = min(maximum - value, value - minimum);

    return weight;
}
'''
        else:
            functions += '''
float calculateWeight( float value, float minimum, float maximum )
{
    value = clamp(value, minimum, maximum);
    float weight = min(maximum - value, value - minimum);

    return weight;
}
'''

        functions += '''
float calculateFinalWeight( float height, float slope, float4 limits )
{
    return calculateWeight(height, limits.x, limits.y)
           * calculateWeight(slope, limits.z, limits.a);
}

float3 reflectVector( float3 input, float3 normal)
{
    return ( -2 * dot(input,normal) * normal + input );
}
'''
        return functions
    
    
    def getVertexFragmentConnector(self):
        vfconn ='''
struct vfconn
{
    //from terrain shader
    float2 l_tex_coord : TEXCOORD0;
    float3 l_normal : TEXCOORD1;
    float3 l_world_pos : TEXCOORD2;

    //from auto shader
    float4 l_eye_position : TEXCOORD3;
    float4 l_eye_normal : TEXCOORD4;
'''
        if self.fogDensity:
            vfconn +='''
    float l_fog : FOG;'''

        vfconn +='''
};
'''
        return vfconn
    
    def getVertexShader(self):
        vShader ='''
void vshader(
        in float2 vtx_texcoord0 : TEXCOORD0,
        in float4 vtx_position : POSITION,
        in float4 vtx_normal : NORMAL,

        out vfconn output,
        out float4 l_position : POSITION,

        uniform float fogDensity: FOGDENSITY,
        uniform float3 camPos : CAMPOS,
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
'''
        if self.fogDensity:
            vShader +='''
        // there has to be a faster way to get the camera's coordinates in a shader
        float3 cam_to_vertex = output.l_world_pos - camPos;
        output.l_fog = FogAmount(fogDensity.x, cam_to_vertex);

'''

        vShader +='''
        output.l_normal = vtx_normal.xyz;
        output.l_normal.x *= slopeScale;
        output.l_normal.y *= slopeScale;
        output.l_normal = normalize(output.l_normal);
        //vtx_normal.xyz = output.l_normal;

        //output.l_eye_position = mul(trans_model_to_view, vtx_position);
        //output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
        //output.l_eye_normal = mul(tpose_view_to_model, vtx_normal);
}
'''
        return vShader
    
    def getFragmentShaderTop(self):
        fshader ='''
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
        in uniform float normalMapStrength : NORMALMAPSTRENGTH,
        in uniform float detailSmallScale,
        in uniform float detailBigScale,
        in uniform float detailHugeScale,
        '''
        if self.fogDensity:
            fshader += '''
        in uniform float4 fogColor : FOGCOLOR,
'''
        return fshader
    
    def getFShaderTerrainParameters(self):

        texNum = 0
        regionNum = 0
        string = ''
        for tex in self.textureMapper.textures:
            string += '''
            in uniform sampler2D texUnit''' + str(texNum) + ' : TEXUNIT' + str(texNum) + ','
            texNum += 1
            for region in tex.regions:
                string += '''
                in uniform float4 region''' + str(regionNum) + 'Limits : REGION' + str(regionNum) + 'LIMITS,'
                regionNum += 1
        return string[:-1] #trim last comma


    def getTerrainPrepCode(self):
        fshader = '''
) {
'''
#        if self.fogDensity:
        if False:
            fshader += '''
        if (input.l_fog == 1.0)
        {
            o_color = fogColor;
            return;
        }
'''
        fshader += '''
        //set up texture calculations
        // Fetch all textures.
        float slope = 1.0 - dot( input.l_normal, vec3(0,0,1));
        float height = input.l_world_pos.z;
        float textureWeight = 0.0;
        float textureWeightTotal = 0.000001;
        vec4 terrainColor = float4(0.0, 0.0, 0.0, 1.0);

'''
        return fshader
    
    def getTerrainTextureCode(self):

        texNum = 0
        regionNum = 0
        string = ''
        for tex in self.textureMapper.textures:
            for region in tex.regions:
                texStr = str(texNum)
                regionStr = str(regionNum)
                string += '''

    //texture''' + texStr + ', region ' + regionStr + '''
    textureWeight = calculateFinalWeight(height, slope, region''' + regionStr + '''Limits);'''
                if self.avoidConditionals > 1:
                    string += '''
        textureWeightTotal += textureWeight;
        terrainColor += textureWeight * tex2D(texUnit''' + texStr + ''', input.l_tex_coord);
'''
                else:
                    string += '''
    if (textureWeight)
    {
        textureWeightTotal += textureWeight;
        terrainColor += textureWeight * tex2D(texUnit''' + texStr + ''', input.l_tex_coord);
    }
'''
                regionNum += 1
            texNum += 1
        return string

    
    def getFragmentShaderEnd(self):

        fshader = '''
        // normalize color
        terrainColor /= textureWeightTotal;
        attr_color = terrainColor;
        //attr_color =  float4(1.0,1.0,1.0,1.0); //lighting test

        // detail texture
        float2 detailCoordSmall = input.l_tex_coord * detailSmallScale;
        float2 detailCoordBig = input.l_tex_coord * detailBigScale;
        float2 detailCoordHuge = input.l_tex_coord * detailHugeScale;
        attr_color *= 1.5 * (tex2D(detailTex, detailCoordSmall) * tex2D(detailTex, detailCoordBig) * tex2D(detailTex, detailCoordHuge));
'''
        if self.normalMapping:
            fshader += '''
        // normal mapping
        float3 normalModifier = tex2D(normalMap, detailCoordSmall) + tex2D(normalMap, detailCoordBig) + tex2D(normalMap, detailCoordHuge) - 1.5;
        input.l_normal *= normalModifier.z/normalMapStrength.x;
        input.l_normal.x += normalModifier.x;
        input.l_normal.y += normalModifier.y;
        input.l_normal = normalize(input.l_normal);
'''

        fshader += '''
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
            fshader += '''
        //glare direct sun... should glare on reflection over normal instead.
        dlight_angle -= 0.002 * dlight_angle / (dlight_angle-1.005);
'''
        fshader += '''
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
'''
        if self.fogDensity:
            fshader += '''
        result = lerp( fogColor, result, input.l_fog );
'''
        fshader += '''
        o_color = result * 1.000001;
}
'''
        return fshader
 
    def feedThePanda(self):

        texNum = 0
        regionNum = 0
        for tex in self.textureMapper.textures:
            self.terrain.setShaderInput('texUnit' + str(texNum), tex.tex)
            for region in tex.regions:
                key = 'region' + str(regionNum) + 'Limits'
                value = region
                #self.terrain.shaderRegions[key] = value
                self.terrain.setShaderInput(key, value)
                regionNum += 1
            texNum += 1

    def createShader(self):
        print "loading terrain settings into shader input..."
        self.feedThePanda()

        print "assembling shader cg code"
        shader = self.getHeader()
        shader += self.getFunctions()
        shader += self.getVertexFragmentConnector()
        shader += self.getVertexShader()
        shader += self.getFragmentShaderTop()
        shader += self.getFShaderTerrainParameters()
        shader += self.getTerrainPrepCode()
        shader += self.getTerrainTextureCode()
        shader += self.getFragmentShaderEnd()
        return shader

    def saveShader(self, name='shaders/stephen6.sha'):
        string = self.createShader()
        f = open(name, 'w')
        f.write(string)
