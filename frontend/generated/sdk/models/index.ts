/* tslint:disable */
/* eslint-disable */
/**
 * 
 * @export
 * @interface ArrowInput
 */
export interface ArrowInput {
    /**
     * 
     * @type {number}
     * @memberof ArrowInput
     */
    end_id: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowInput
     */
    arrow_number: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowInput
     */
    score: number;
    /**
     * 
     * @type {ArrowInputScoreMarkEnum}
     * @memberof ArrowInput
     */
    score_mark?: ArrowInputScoreMarkEnum;
    /**
     * 
     * @type {number}
     * @memberof ArrowInput
     */
    x?: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowInput
     */
    y?: number;
    /**
     * 
     * @type {string}
     * @memberof ArrowInput
     */
    notes?: string;
}


/**
 * @export
 */
export const ArrowInputScoreMarkEnum = {
    empty: '',
    X: 'X',
    M: 'M'
} as const;
export type ArrowInputScoreMarkEnum = typeof ArrowInputScoreMarkEnum[keyof typeof ArrowInputScoreMarkEnum];

/**
 * 
 * @export
 * @interface ArrowRecord
 */
export interface ArrowRecord {
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    id: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    end_id: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    arrow_number: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    score: number;
    /**
     * 
     * @type {ArrowRecordScoreMarkEnum}
     * @memberof ArrowRecord
     */
    score_mark: ArrowRecordScoreMarkEnum;
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    x: number;
    /**
     * 
     * @type {number}
     * @memberof ArrowRecord
     */
    y: number;
    /**
     * 
     * @type {string}
     * @memberof ArrowRecord
     */
    notes: string;
    /**
     * 
     * @type {string}
     * @memberof ArrowRecord
     */
    created_at: string;
}


/**
 * @export
 */
export const ArrowRecordScoreMarkEnum = {
    empty: '',
    X: 'X',
    M: 'M'
} as const;
export type ArrowRecordScoreMarkEnum = typeof ArrowRecordScoreMarkEnum[keyof typeof ArrowRecordScoreMarkEnum];

/**
 * 
 * @export
 * @interface EndInput
 */
export interface EndInput {
    /**
     * 
     * @type {number}
     * @memberof EndInput
     */
    round_id: number;
    /**
     * 
     * @type {number}
     * @memberof EndInput
     */
    end_number?: number;
    /**
     * 
     * @type {string}
     * @memberof EndInput
     */
    notes?: string;
}
/**
 * 
 * @export
 * @interface EndRecord
 */
export interface EndRecord {
    /**
     * 
     * @type {number}
     * @memberof EndRecord
     */
    id: number;
    /**
     * 
     * @type {number}
     * @memberof EndRecord
     */
    round_id: number;
    /**
     * 
     * @type {number}
     * @memberof EndRecord
     */
    end_number: number;
    /**
     * 
     * @type {string}
     * @memberof EndRecord
     */
    notes: string;
    /**
     * 
     * @type {number}
     * @memberof EndRecord
     */
    total_score: number;
    /**
     * 
     * @type {string}
     * @memberof EndRecord
     */
    created_at: string;
}
/**
 * 
 * @export
 * @interface ErrorResponse
 */
export interface ErrorResponse {
    /**
     * 
     * @type {string}
     * @memberof ErrorResponse
     */
    message: string;
}
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

/**
 * 
 * @export
 * @interface LoginInput
 */
export interface LoginInput {
    /**
     * 
     * @type {string}
     * @memberof LoginInput
     */
    username: string;
    /**
     * 
     * @type {string}
     * @memberof LoginInput
     */
    password: string;
}
/**
 * 
 * @export
 * @interface LoginResponse
 */
export interface LoginResponse {
    /**
     * 
     * @type {boolean}
     * @memberof LoginResponse
     */
    created: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof LoginResponse
     */
    password_initialized?: boolean;
    /**
     * 
     * @type {UserRecord}
     * @memberof LoginResponse
     */
    user: UserRecord;
}
/**
 * 
 * @export
 * @interface PracticeInput
 */
export interface PracticeInput {
    /**
     * 
     * @type {number}
     * @memberof PracticeInput
     */
    user_id: number;
    /**
     * 
     * @type {number}
     * @memberof PracticeInput
     */
    distance_meters?: number;
    /**
     * 
     * @type {number}
     * @memberof PracticeInput
     */
    target_face_cm?: number;
    /**
     * 
     * @type {string}
     * @memberof PracticeInput
     */
    notes?: string;
}
/**
 * 
 * @export
 * @interface PracticeRecord
 */
export interface PracticeRecord {
    /**
     * 
     * @type {number}
     * @memberof PracticeRecord
     */
    id: number;
    /**
     * 
     * @type {number}
     * @memberof PracticeRecord
     */
    user_id: number;
    /**
     * 
     * @type {number}
     * @memberof PracticeRecord
     */
    distance_meters: number;
    /**
     * 
     * @type {number}
     * @memberof PracticeRecord
     */
    target_face_cm: number;
    /**
     * 
     * @type {string}
     * @memberof PracticeRecord
     */
    notes: string;
    /**
     * 
     * @type {string}
     * @memberof PracticeRecord
     */
    created_at: string;
}
/**
 * 
 * @export
 * @interface RoundInput
 */
export interface RoundInput {
    /**
     * 
     * @type {number}
     * @memberof RoundInput
     */
    practice_id: number;
    /**
     * 
     * @type {string}
     * @memberof RoundInput
     */
    name: string;
    /**
     * 
     * @type {string}
     * @memberof RoundInput
     */
    notes?: string;
}
/**
 * 
 * @export
 * @interface RoundRecord
 */
export interface RoundRecord {
    /**
     * 
     * @type {number}
     * @memberof RoundRecord
     */
    id: number;
    /**
     * 
     * @type {number}
     * @memberof RoundRecord
     */
    practice_id: number;
    /**
     * 
     * @type {number}
     * @memberof RoundRecord
     */
    round_order: number;
    /**
     * 
     * @type {string}
     * @memberof RoundRecord
     */
    name: string;
    /**
     * 
     * @type {string}
     * @memberof RoundRecord
     */
    notes: string;
    /**
     * 
     * @type {number}
     * @memberof RoundRecord
     */
    total_score: number;
    /**
     * 
     * @type {string}
     * @memberof RoundRecord
     */
    created_at: string;
}
/**
 * 
 * @export
 * @interface UserInput
 */
export interface UserInput {
    /**
     * 
     * @type {string}
     * @memberof UserInput
     */
    name: string;
    /**
     * Required on create. Leave empty on update to keep the current password.
     * @type {string}
     * @memberof UserInput
     */
    password?: string;
}
/**
 * 
 * @export
 * @interface UserRecord
 */
export interface UserRecord {
    /**
     * 
     * @type {number}
     * @memberof UserRecord
     */
    id: number;
    /**
     * 
     * @type {string}
     * @memberof UserRecord
     */
    name: string;
    /**
     * 
     * @type {string}
     * @memberof UserRecord
     */
    created_at: string;
}
