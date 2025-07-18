declare module 'leaflet' {
  export class Map {
    constructor(id: string | HTMLElement, options?: MapOptions);
    setView(center: LatLngExpression, zoom: number, options?: ZoomPanOptions): this;
    addLayer(layer: Layer): this;
    removeLayer(layer: Layer): this;
    getCenter(): LatLng;
    getZoom(): number;
    setZoom(zoom: number): this;
    fitBounds(bounds: LatLngBoundsExpression, options?: FitBoundsOptions): this;
    invalidateSize(options?: ZoomPanOptions): this;
  }

  export interface MapOptions {
    center?: LatLngExpression;
    zoom?: number;
    layers?: Layer[];
    minZoom?: number;
    maxZoom?: number;
    maxBounds?: LatLngBoundsExpression;
    renderer?: Renderer;
    zoomControl?: boolean;
    attributionControl?: boolean;
    [name: string]: any;
  }

  export interface LatLng {
    lat: number;
    lng: number;
    alt?: number;
  }

  export type LatLngExpression = LatLng | [number, number] | [number, number, number];
  export type LatLngBoundsExpression = LatLngBounds | LatLngExpression[];

  export interface LatLngBounds {
    extend(latlng: LatLngExpression): this;
    getSouthWest(): LatLng;
    getNorthEast(): LatLng;
    getCenter(): LatLng;
  }

  export interface Layer {
    addTo(map: Map): this;
    remove(): this;
    removeFrom(map: Map): this;
  }

  export interface ZoomPanOptions {
    animate?: boolean;
    duration?: number;
    easeLinearity?: number;
    noMoveStart?: boolean;
  }

  export interface FitBoundsOptions extends ZoomPanOptions {
    paddingTopLeft?: PointExpression;
    paddingBottomRight?: PointExpression;
    padding?: PointExpression;
    maxZoom?: number;
  }

  export interface Point {
    x: number;
    y: number;
  }

  export type PointExpression = Point | [number, number];

  export interface Renderer extends Layer {}

  export namespace control {
    function scale(options?: ScaleOptions): Control;
    function zoom(options?: ZoomOptions): Control;
    function layers(baseLayers?: Record<string, Layer>, overlays?: Record<string, Layer>, options?: LayersControlOptions): Control;
  }
  
  export interface ScaleOptions {
    maxWidth?: number;
    metric?: boolean;
    imperial?: boolean;
    updateWhenIdle?: boolean;
    position?: ControlPosition;
  }
  
  export interface ZoomOptions {
    position?: ControlPosition;
    zoomInText?: string;
    zoomInTitle?: string;
    zoomOutText?: string;
    zoomOutTitle?: string;
  }
  
  export interface LayersControlOptions {
    position?: ControlPosition;
    collapsed?: boolean;
  }
  
  export type ControlPosition = 'topleft' | 'topright' | 'bottomleft' | 'bottomright';

  export interface Control {
    addTo(map: Map): this;
    remove(): this;
    getPosition(): ControlPosition;
    setPosition(position: ControlPosition): this;
    onAdd?(map: Map): HTMLElement;
    onRemove?(map: Map): void;
  }

  export function map(id: string | HTMLElement, options?: MapOptions): Map;
  
  export function tileLayer(urlTemplate: string, options?: TileLayerOptions): TileLayer;
  
  export function marker(latlng: LatLngExpression, options?: MarkerOptions): Marker;
  
  export function polygon(latlngs: LatLngExpression[], options?: PolylineOptions): Polygon;
  
  export function control(options?: ControlOptions): Control;
  
  export namespace DomUtil {
    function create(tagName: string, className?: string, container?: HTMLElement): HTMLElement;
  }
  
  export interface TileLayerOptions {
    attribution?: string;
    minZoom?: number;
    maxZoom?: number;
    maxNativeZoom?: number;
    minNativeZoom?: number;
    subdomains?: string | string[];
    errorTileUrl?: string;
    zoomOffset?: number;
    tms?: boolean;
    zoomReverse?: boolean;
    detectRetina?: boolean;
    crossOrigin?: boolean | string;
    [name: string]: any;
  }
  
  export interface Marker extends Layer {
    getLatLng(): LatLng;
    setLatLng(latlng: LatLngExpression): this;
    setIcon(icon: Icon): this;
    setZIndexOffset(offset: number): this;
    setOpacity(opacity: number): this;
    bindPopup(content: string | HTMLElement | Function | Popup, options?: PopupOptions): this;
    unbindPopup(): this;
    openPopup(latlng?: LatLngExpression): this;
    closePopup(): this;
    togglePopup(): this;
    isPopupOpen(): boolean;
    toGeoJSON(): any;
  }
  
  export interface MarkerOptions {
    icon?: Icon;
    keyboard?: boolean;
    title?: string;
    alt?: string;
    zIndexOffset?: number;
    opacity?: number;
    riseOnHover?: boolean;
    riseOffset?: number;
    pane?: string;
    shadowPane?: string;
    bubblingMouseEvents?: boolean;
  }
  
  export interface ControlOptions {
    position?: ControlPosition;
  }
  
  export interface Icon {
    createIcon(oldIcon?: HTMLElement): HTMLElement;
    createShadow(oldIcon?: HTMLElement): HTMLElement;
  }
  
  export interface IconOptions {
    iconUrl?: string;
    iconRetinaUrl?: string;
    iconSize?: PointExpression;
    iconAnchor?: PointExpression;
    popupAnchor?: PointExpression;
    shadowUrl?: string;
    shadowRetinaUrl?: string;
    shadowSize?: PointExpression;
    shadowAnchor?: PointExpression;
    className?: string;
  }
  
  export interface DivIconOptions extends IconOptions {
    html?: string | HTMLElement;
    bgPos?: PointExpression;
  }
  
  export function divIcon(options?: DivIconOptions): Icon;
  
  export interface PolylineOptions {
    stroke?: boolean;
    color?: string;
    weight?: number;
    opacity?: number;
    lineCap?: string;
    lineJoin?: string;
    dashArray?: string;
    dashOffset?: string;
    fill?: boolean;
    fillColor?: string;
    fillOpacity?: number;
    fillRule?: string;
    bubblingMouseEvents?: boolean;
    renderer?: Renderer;
    className?: string;
    interactive?: boolean;
  }

  export interface Polyline extends Layer {
    toGeoJSON(): any;
    getLatLngs(): LatLng[][];
    setLatLngs(latlngs: LatLngExpression[]): this;
    isEmpty(): boolean;
    getCenter(): LatLng;
    getBounds(): LatLngBounds;
    addLatLng(latlng: LatLngExpression): this;
  }

  export interface Polygon extends Polyline {
    getBounds(): LatLngBounds;
  }

  export interface Popup {
    openOn(map: Map): this;
    setLatLng(latlng: LatLngExpression): this;
    setContent(htmlContent: string | HTMLElement): this;
    getLatLng(): LatLng;
    getContent(): string | HTMLElement;
    update(): void;
  }
  
  export interface PopupOptions {
    maxWidth?: number;
    minWidth?: number;
    maxHeight?: number;
    autoPan?: boolean;
    autoPanPaddingTopLeft?: PointExpression;
    autoPanPaddingBottomRight?: PointExpression;
    autoPanPadding?: PointExpression;
    keepInView?: boolean;
    closeButton?: boolean;
    autoClose?: boolean;
    closeOnEscapeKey?: boolean;
    className?: string;
  }
  
  export function popup(options?: PopupOptions, source?: Layer): Popup;
  
  export interface TileLayer extends Layer {
    setUrl(url: string, noRedraw?: boolean): this;
    getContainer(): HTMLElement | null;
    setOpacity(opacity: number): this;
    getAttribution(): string | null;
    getEvents(): { [name: string]: Function };
    getTileSize(): Point;
  }
}