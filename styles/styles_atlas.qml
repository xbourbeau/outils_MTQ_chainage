<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" symbologyReferenceScale="-1" maxScale="0" simplifyLocal="1" version="3.34.0-Prizren" simplifyAlgorithm="0" labelsEnabled="1" styleCategories="LayerConfiguration|Symbology|Labeling|Fields|MapTips|Rendering" minScale="100000000" simplifyDrawingTol="1" simplifyMaxScale="1" readOnly="0" simplifyDrawingHints="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <renderer-v2 forceraster="0" type="singleSymbol" referencescale="-1" enableorderby="0" symbollevels="0">
    <symbols>
      <symbol alpha="1" name="0" clip_to_extent="1" force_rhr="0" is_animated="0" type="fill" frame_rate="10">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer class="SimpleFill" pass="0" id="{da63c7d7-b510-4859-a1c5-4ef3007f0d5f}" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="182,24,27,128"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="fillColor" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="if($id % 2 = 0, color_rgba(24, 90, 182, 100), color_rgba(182, 24, 27, 100))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol alpha="1" name="" clip_to_extent="1" force_rhr="0" is_animated="0" type="fill" frame_rate="10">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer class="SimpleFill" pass="0" id="{7a078ac8-a167-48f5-a43d-b538ec9817ab}" locked="0" enabled="1">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="color" type="QString" value="0,0,255,255"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.26"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="style" type="QString" value="solid"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontUnderline="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSize="10" capitalization="0" multilineHeightUnit="Percentage" isExpression="1" fontSizeUnit="Point" fontLetterSpacing="0" blendMode="0" legendString="Aa" fontItalic="1" multilineHeight="1" namedStyle="Bold Italic" fontWeight="75" fieldName="'Page ' + to_string($id)" allowHtml="0" textOrientation="horizontal" previewBkgrdColor="255,255,255,255" forcedBold="0" fontKerning="1" forcedItalic="0" fontWordSpacing="0" useSubstitutions="0" textOpacity="1" fontFamily="Arial" textColor="255,255,255,255" fontStrikeout="0">
        <families/>
        <text-buffer bufferOpacity="1" bufferColor="0,0,0,255" bufferSize="0.59999999999999998" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferBlendMode="0" bufferDraw="1" bufferNoFill="0" bufferSizeUnits="MM"/>
        <text-mask maskSizeUnits="MM" maskEnabled="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskedSymbolLayers="" maskSize="0" maskOpacity="1" maskJoinStyle="128" maskType="0"/>
        <background shapeRadiiX="0" shapeRotation="0" shapeJoinStyle="64" shapeSizeType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeSizeX="0" shapeBorderWidth="0" shapeSVGFile="" shapeFillColor="255,255,255,255" shapeType="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeRadiiUnit="Point" shapeDraw="0" shapeRotationType="0" shapeOpacity="1" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="Point" shapeRadiiY="0" shapeOffsetUnit="Point" shapeSizeUnit="Point" shapeSizeY="0" shapeBorderColor="128,128,128,255">
          <symbol alpha="1" name="markerSymbol" clip_to_extent="1" force_rhr="0" is_animated="0" type="marker" frame_rate="10">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer class="SimpleMarker" pass="0" id="" locked="0" enabled="1">
              <Option type="Map">
                <Option name="angle" type="QString" value="0"/>
                <Option name="cap_style" type="QString" value="square"/>
                <Option name="color" type="QString" value="243,166,178,255"/>
                <Option name="horizontal_anchor_point" type="QString" value="1"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="name" type="QString" value="circle"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="35,35,35,255"/>
                <Option name="outline_style" type="QString" value="solid"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="outline_width_unit" type="QString" value="MM"/>
                <Option name="scale_method" type="QString" value="diameter"/>
                <Option name="size" type="QString" value="2"/>
                <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="size_unit" type="QString" value="MM"/>
                <Option name="vertical_anchor_point" type="QString" value="1"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol alpha="1" name="fillSymbol" clip_to_extent="1" force_rhr="0" is_animated="0" type="fill" frame_rate="10">
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" type="QString" value=""/>
                <Option name="properties"/>
                <Option name="type" type="QString" value="collection"/>
              </Option>
            </data_defined_properties>
            <layer class="SimpleFill" pass="0" id="" locked="0" enabled="1">
              <Option type="Map">
                <Option name="border_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="color" type="QString" value="255,255,255,255"/>
                <Option name="joinstyle" type="QString" value="bevel"/>
                <Option name="offset" type="QString" value="0,0"/>
                <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
                <Option name="offset_unit" type="QString" value="MM"/>
                <Option name="outline_color" type="QString" value="128,128,128,255"/>
                <Option name="outline_style" type="QString" value="no"/>
                <Option name="outline_width" type="QString" value="0"/>
                <Option name="outline_width_unit" type="QString" value="Point"/>
                <Option name="style" type="QString" value="solid"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option name="name" type="QString" value=""/>
                  <Option name="properties"/>
                  <Option name="type" type="QString" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowColor="0,0,0,255" shadowOffsetGlobal="1" shadowScale="100" shadowOffsetDist="1" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusAlphaOnly="0" shadowDraw="0" shadowOffsetAngle="135" shadowOffsetUnit="Point" shadowRadius="1.5" shadowRadiusUnit="Point" shadowUnder="0" shadowOpacity="1" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowBlendMode="6"/>
        <dd_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format placeDirectionSymbol="0" autoWrapLength="0" wrapChar="" addDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" reverseDirectionSymbol="0" decimals="3" leftDirectionSymbol="&lt;" multilineAlign="3" rightDirectionSymbol=">" formatNumbers="0" plussign="0"/>
      <placement overrunDistanceUnit="MM" fitInPolygonOnly="0" offsetType="0" lineAnchorTextPoint="FollowPlacement" distUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" overlapHandling="PreventOverlap" lineAnchorType="0" quadOffset="4" dist="0" yOffset="0" distMapUnitScale="3x:0,0,0,0,0,0" rotationUnit="AngleDegrees" maxCurvedCharAngleIn="25" repeatDistance="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" rotationAngle="0" geometryGenerator="" placement="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" geometryGeneratorType="PointGeometry" centroidInside="0" allowDegraded="0" layerType="PolygonGeometry" repeatDistanceUnits="MM" placementFlags="10" lineAnchorClipping="0" priority="5" geometryGeneratorEnabled="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" lineAnchorPercent="0.5" maxCurvedCharAngleOut="-25" overrunDistance="0" xOffset="0" polygonPlacementFlags="2" centroidWhole="0" preserveRotation="1"/>
      <rendering labelPerPart="0" scaleMin="0" unplacedVisibility="0" mergeLines="0" maxNumLabels="2000" scaleVisibility="1" fontMinPixelSize="3" obstacleType="1" obstacleFactor="1" scaleMax="10000" drawLabels="1" obstacle="1" zIndex="0" limitNumLabels="0" fontLimitPixelSize="0" fontMaxPixelSize="10000" minFeatureSize="0" upsidedownLabels="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties" type="Map">
            <Option name="BufferColor" type="Map">
              <Option name="active" type="bool" value="true"/>
              <Option name="expression" type="QString" value="if($id % 2 = 0, color_rgba(24, 90, 182, 100), color_rgba(182, 24, 27, 100))"/>
              <Option name="type" type="int" value="3"/>
            </Option>
          </Option>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option name="anchorPoint" type="QString" value="pole_of_inaccessibility"/>
          <Option name="blendMode" type="int" value="0"/>
          <Option name="ddProperties" type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
          <Option name="drawToAllParts" type="bool" value="false"/>
          <Option name="enabled" type="QString" value="0"/>
          <Option name="labelAnchorPoint" type="QString" value="point_on_exterior"/>
          <Option name="lineSymbol" type="QString" value="&lt;symbol alpha=&quot;1&quot; name=&quot;symbol&quot; clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot; is_animated=&quot;0&quot; type=&quot;line&quot; frame_rate=&quot;10&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer class=&quot;SimpleLine&quot; pass=&quot;0&quot; id=&quot;{863d4085-1bfa-4374-b852-e37b00c538b1}&quot; locked=&quot;0&quot; enabled=&quot;1&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;align_dash_pattern&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;capstyle&quot; type=&quot;QString&quot; value=&quot;square&quot;/>&lt;Option name=&quot;customdash&quot; type=&quot;QString&quot; value=&quot;5;2&quot;/>&lt;Option name=&quot;customdash_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;customdash_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;dash_pattern_offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;dash_pattern_offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;dash_pattern_offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;draw_inside_polygon&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;joinstyle&quot; type=&quot;QString&quot; value=&quot;bevel&quot;/>&lt;Option name=&quot;line_color&quot; type=&quot;QString&quot; value=&quot;60,60,60,255&quot;/>&lt;Option name=&quot;line_style&quot; type=&quot;QString&quot; value=&quot;solid&quot;/>&lt;Option name=&quot;line_width&quot; type=&quot;QString&quot; value=&quot;0.3&quot;/>&lt;Option name=&quot;line_width_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;offset&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;offset_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;offset_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;ring_filter&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_end_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_end_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;trim_distance_start&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;trim_distance_start_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;Option name=&quot;trim_distance_start_unit&quot; type=&quot;QString&quot; value=&quot;MM&quot;/>&lt;Option name=&quot;tweak_dash_pattern_on_corners&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;use_custom_dash&quot; type=&quot;QString&quot; value=&quot;0&quot;/>&lt;Option name=&quot;width_map_unit_scale&quot; type=&quot;QString&quot; value=&quot;3x:0,0,0,0,0,0&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option name=&quot;name&quot; type=&quot;QString&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option name=&quot;type&quot; type=&quot;QString&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option name="minLength" type="double" value="0"/>
          <Option name="minLengthMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="minLengthUnit" type="QString" value="MM"/>
          <Option name="offsetFromAnchor" type="double" value="0"/>
          <Option name="offsetFromAnchorMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromAnchorUnit" type="QString" value="MM"/>
          <Option name="offsetFromLabel" type="double" value="0"/>
          <Option name="offsetFromLabelMapUnitScale" type="QString" value="3x:0,0,0,0,0,0"/>
          <Option name="offsetFromLabelUnit" type="QString" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <fieldConfiguration>
    <field name="rtss" configurationFlags="NoFlag"/>
    <field name="chainage_d" configurationFlags="NoFlag"/>
    <field name="chainage_f" configurationFlags="NoFlag"/>
    <field name="angle" configurationFlags="NoFlag"/>
  </fieldConfiguration>
  <aliases>
    <alias name="" index="0" field="rtss"/>
    <alias name="" index="1" field="chainage_d"/>
    <alias name="" index="2" field="chainage_f"/>
    <alias name="" index="3" field="angle"/>
  </aliases>
  <splitPolicies>
    <policy field="rtss" policy="Duplicate"/>
    <policy field="chainage_d" policy="Duplicate"/>
    <policy field="chainage_f" policy="Duplicate"/>
    <policy field="angle" policy="Duplicate"/>
  </splitPolicies>
  <defaults>
    <default expression="" field="rtss" applyOnUpdate="0"/>
    <default expression="" field="chainage_d" applyOnUpdate="0"/>
    <default expression="" field="chainage_f" applyOnUpdate="0"/>
    <default expression="" field="angle" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="rtss"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="chainage_d"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="chainage_f"/>
    <constraint exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0" field="angle"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="rtss"/>
    <constraint exp="" desc="" field="chainage_d"/>
    <constraint exp="" desc="" field="chainage_f"/>
    <constraint exp="" desc="" field="angle"/>
  </constraintExpressions>
  <expressionfields/>
  <previewExpression>"rtss"</previewExpression>
  <mapTip enabled="1"></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
