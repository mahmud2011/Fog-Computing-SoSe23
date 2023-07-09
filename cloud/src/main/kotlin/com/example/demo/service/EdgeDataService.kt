package com.example.demo.service

import com.example.demo.dto.EdgeDataDTO
import com.example.demo.repository.EdgeDataRepository
import com.example.demo.repository.UserTokenRepository
import org.springframework.messaging.simp.SimpMessagingTemplate
import org.springframework.stereotype.Service

@Service
class EdgeDataService(
    val edgeDataRepository: EdgeDataRepository,
    val userTokenRepository: UserTokenRepository
) {
    fun saveEdgeData(edgeData: EdgeDataDTO): EdgeDataDTO {
        val userTokenRecord = userTokenRepository.findByToken(edgeData.token)!!
        edgeData.id = edgeDataRepository.save(edgeData.toEdgeDataEntity(userTokenRecord)).id

        return edgeData
    }

    fun updateEdgeData(edgeData: EdgeDataDTO) {
        val edgeDataRecord = edgeData.id?.let { edgeDataRepository.findById(it) }
        edgeDataRecord?.ifPresent {
            it.data = edgeData.data
            edgeDataRepository.save(it)
        }
    }

    fun getAllEdgeData(): List<EdgeDataDTO>? {
        return edgeDataRepository.findAll().map {
            return@map EdgeDataDTO(
                id = it.id,
                data = it.data!!,
                token = ""
            )
        }
    }
}