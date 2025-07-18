/// <reference types="leaflet" />

declare module 'geoportal-extensions-leaflet' {}

declare namespace L {
  export namespace geoportalLayer {
    function WMTS(options: WMTSOptions): any;
    function WMS(options: WMSOptions): any;
  }

  export interface WMTSOptions {
    layer: string;
    apiKey: string;
    [key: string]: any;
  }

  export interface WMSOptions {
    layer: string;
    apiKey: string;
    [key: string]: any;
  }
}