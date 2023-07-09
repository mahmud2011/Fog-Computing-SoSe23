package com.example.demo.dto

import com.example.demo.model.EdgeDataEntity
import com.example.demo.model.UserTokenEntity

data class EdgeDataDTO (
    val data: Map<String, Any>,
    var id: Long? = null,
    val token: String) {
    fun toEdgeDataEntity(userTokenRecord: UserTokenEntity): EdgeDataEntity {
        return EdgeDataEntity(data = data).apply { userToken = userTokenRecord }
    }
}