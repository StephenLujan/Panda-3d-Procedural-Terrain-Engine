"""
fullterrainshadergenerator.py:
"""
__author__ = "Stephen Lujan"

from terrainshadergenerator import *

###############################################################################
#   FullTerrainShaderGenerator
###############################################################################

class FullTerrainShaderGenerator(TerrainShaderGenerator):

    def getVertexFragmentConnector(self):
        vfconn = '''
struct vfconn
{
    //from terrain shader
    float2 l_tex_coord : TEXCOORD0;
    float3 l_normal : TEXCOORD1;
    float3 l_world_pos : TEXCOORD6;
    float4 l_color : COLOR;

    //from auto shader
    float3 l_eye_position : TEXCOORD2;
    float3 l_eye_normal : TEXCOORD3;
    float3 l_eyeVec : TEXCOORD4;
'''
        if self.fogDensity:
            vfconn += '''
    float l_fog : FOG;
'''
        vfconn += '''
};
'''
        return vfconn

    def getFShaderTerrainParameters(self):

        texNum = 0
        regionNum = 0
        string = ''
        for tex in self.textureMapper.textures:
            string += '''
            in uniform sampler2D texUnit''' + str(texNum) + ','
            texNum += 1
            for region in tex.regions:
                string += '''
                in uniform float4 region''' + str(regionNum) + 'Limits,'
                regionNum += 1
        string = string[:-1] #trim last comma
        string +='''
) {
'''
        return string


    def getTerrainPrepCode(self):
        fshader = ''
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
        float slope = 1.0 - dot( terrainNormal, vec3(0,0,1));
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
        string += """
        // normalize color
        terrainColor /= textureWeightTotal;
        attr_color = terrainColor;
        //attr_color =  float4(1.0,1.0,1.0,1.0); //lighting test
"""
        return string

    def initializeShaderInput(self):

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

    def saveShader(self, name='shaders/FullTerrain.sha'):
        TerrainShaderGenerator.saveShader(self, name)
