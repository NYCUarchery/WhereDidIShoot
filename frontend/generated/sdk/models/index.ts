/* tslint:disable */
/* eslint-disable */
/**
 * 
 * @export
 * @interface HealthResponse
 */
export interface HealthResponse {
    /**
     * 
     * @type {HealthResponseStatusEnum}
     * @memberof HealthResponse
     */
    status: HealthResponseStatusEnum;
    /**
     * 
     * @type {string}
     * @memberof HealthResponse
     */
    service: string;
    /**
     * 
     * @type {HealthResponseDatabaseEnum}
     * @memberof HealthResponse
     */
    database: HealthResponseDatabaseEnum;
    /**
     * 
     * @type {string}
     * @memberof HealthResponse
     */
    timestamp: string;
}


/**
 * @export
 */
export const HealthResponseStatusEnum = {
    ok: 'ok',
    degraded: 'degraded'
} as const;
export type HealthResponseStatusEnum = typeof HealthResponseStatusEnum[keyof typeof HealthResponseStatusEnum];

/**
 * @export
 */
export const HealthResponseDatabaseEnum = {
    connected: 'connected',
    unavailable: 'unavailable'
} as const;
export type HealthResponseDatabaseEnum = typeof HealthResponseDatabaseEnum[keyof typeof HealthResponseDatabaseEnum];

